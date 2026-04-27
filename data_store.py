"""
data_store.py — 数据存储层
负责读写 Obsidian 兼容的 Markdown 待办文件。

文件格式示例（YYYY-MM-DD.md）：
---
date: 2026-04-27
done: 2/5
---
- [x] 已完成的待办 #p/high
- [ ] 未完成的待办 #p/mid
- [ ] 低优先级待办 #p/low
"""

import os
import re
from datetime import datetime, date, timedelta
from typing import List, Optional


# 优先级常量
PRIORITY_HIGH = "high"   # 红色
PRIORITY_MID = "mid"     # 黄色
PRIORITY_LOW = "low"     # 蓝色
PRIORITY_ORDER = [PRIORITY_HIGH, PRIORITY_MID, PRIORITY_LOW]
PRIORITY_DEFAULT = PRIORITY_MID


class TodoItem:
    """单条待办"""

    def __init__(self, text: str, done: bool = False,
                 priority: str = PRIORITY_DEFAULT,
                 created_at: Optional[str] = None):
        self.text = text.strip()
        self.done = done
        self.priority = priority if priority in PRIORITY_ORDER else PRIORITY_DEFAULT
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def cycle_priority(self):
        """循环切换优先级：红→黄→蓝→红"""
        idx = PRIORITY_ORDER.index(self.priority)
        self.priority = PRIORITY_ORDER[(idx + 1) % len(PRIORITY_ORDER)]

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "done": self.done,
            "priority": self.priority,
            "created_at": self.created_at,
        }

    def to_markdown_line(self) -> str:
        checkbox = "[x]" if self.done else "[ ]"
        return f"- {checkbox} {self.text} #p/{self.priority}"

    @staticmethod
    def from_markdown_line(line: str) -> Optional["TodoItem"]:
        """从 Markdown 行解析待办项"""
        line = line.strip()
        # 匹配带优先级标签的格式
        match = re.match(r"^- \[([ xX])\] (.+?)(?:\s+#p/(high|mid|low))?\s*$", line)
        if match:
            done = match.group(1).lower() == "x"
            text = match.group(2).strip()
            priority = match.group(3) or PRIORITY_DEFAULT
            return TodoItem(text=text, done=done, priority=priority)
        return None


class DataStore:
    """数据存储管理器"""

    def __init__(self, base_dir: str):
        """
        base_dir: 待办文件存储根目录
        例如: F:\\Obsidian\\Libo\\daily_todo
        """
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _file_path(self, target_date: date) -> str:
        """获取指定日期的文件路径"""
        filename = target_date.strftime("%Y-%m-%d") + ".md"
        return os.path.join(self.base_dir, filename)

    def load_todos(self, target_date: date) -> List[TodoItem]:
        """加载指定日期的待办列表"""
        filepath = self._file_path(target_date)
        if not os.path.exists(filepath):
            return []

        todos = []
        in_frontmatter = False
        frontmatter_count = 0

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped == "---":
                        frontmatter_count += 1
                        if frontmatter_count == 1:
                            in_frontmatter = True
                        elif frontmatter_count == 2:
                            in_frontmatter = False
                        continue
                    if in_frontmatter:
                        continue
                    if stripped == "":
                        continue
                    item = TodoItem.from_markdown_line(stripped)
                    if item:
                        todos.append(item)
        except Exception as e:
            print(f"[DataStore] 读取文件失败: {filepath}, 错误: {e}")

        return todos

    def save_todos(self, target_date: date, todos: List[TodoItem],
                   mood: Optional[str] = None, slogan: Optional[str] = None):
        """保存待办列表到指定日期的文件（mood/slogan 不传则保留原值）"""
        filepath = self._file_path(target_date)

        # 如果 mood/slogan 没传,从已存文件继承
        if mood is None or slogan is None:
            existing = self.load_metadata(target_date)
            if mood is None:
                mood = existing.get("mood", "")
            if slogan is None:
                slogan = existing.get("slogan", "")

        done_count = sum(1 for t in todos if t.done)
        total_count = len(todos)

        lines = [
            "---\n",
            f"date: {target_date.strftime('%Y-%m-%d')}\n",
            f"done: {done_count}/{total_count}\n",
        ]
        if mood:
            lines.append(f"mood: {mood}\n")
        if slogan:
            escaped = slogan.replace('"', '\\"')
            lines.append(f'slogan: "{escaped}"\n')
        lines.append("tags: [daily_todo]\n")
        lines.append("---\n")

        if todos:
            lines.append("\n")
            for item in todos:
                lines.append(item.to_markdown_line() + "\n")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            print(f"[DataStore] 保存文件失败: {filepath}, 错误: {e}")

    def load_metadata(self, target_date: date) -> dict:
        """读取 frontmatter 中的 mood / slogan"""
        filepath = self._file_path(target_date)
        result = {"mood": "", "slogan": ""}
        if not os.path.exists(filepath):
            return result
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                in_fm = False
                count = 0
                for line in f:
                    stripped = line.strip()
                    if stripped == "---":
                        count += 1
                        if count == 1:
                            in_fm = True
                        elif count == 2:
                            break
                        continue
                    if not in_fm:
                        continue
                    if stripped.startswith("mood:"):
                        result["mood"] = stripped.split(":", 1)[1].strip()
                    elif stripped.startswith("slogan:"):
                        val = stripped.split(":", 1)[1].strip()
                        if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
                            val = val[1:-1].replace('\\"', '"')
                        result["slogan"] = val
        except Exception as e:
            print(f"[DataStore] 读取 metadata 失败: {filepath}, 错误: {e}")
        return result

    def ensure_today_file(self) -> date:
        """确保今天的文件存在，返回今天的日期"""
        today = date.today()
        filepath = self._file_path(today)
        if not os.path.exists(filepath):
            self.save_todos(today, [])
        return today

    def get_available_dates(self) -> List[date]:
        """获取所有有记录的日期列表"""
        dates = []
        if not os.path.exists(self.base_dir):
            return dates

        for filename in os.listdir(self.base_dir):
            match = re.match(r"^(\d{4}-\d{2}-\d{2})\.md$", filename)
            if match:
                try:
                    d = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                    dates.append(d)
                except ValueError:
                    continue

        dates.sort(reverse=True)
        return dates

    def get_week_stats(self, target_date: date) -> tuple:
        """
        获取目标日期所在周的完成率统计
        返回 (done_count, total_count)
        """
        # 计算本周一
        weekday = target_date.weekday()  # 0=Monday
        monday = target_date - timedelta(days=weekday)

        total_done = 0
        total_items = 0

        for i in range(7):
            day = monday + timedelta(days=i)
            if day > date.today():
                break
            todos = self.load_todos(day)
            total_done += sum(1 for t in todos if t.done)
            total_items += len(todos)

        return total_done, total_items
