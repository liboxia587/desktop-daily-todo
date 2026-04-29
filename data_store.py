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
import shutil
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
        """获取指定日期的文件路径(根目录,active 写入位置)"""
        filename = target_date.strftime("%Y-%m-%d") + ".md"
        return os.path.join(self.base_dir, filename)

    def _archive_dir(self) -> str:
        """归档子目录路径"""
        return os.path.join(self.base_dir, "archive")

    def _archive_path(self, target_date: date) -> str:
        """归档后的文件路径"""
        filename = target_date.strftime("%Y-%m-%d") + ".md"
        return os.path.join(self._archive_dir(), filename)

    def _resolve_path(self, target_date: date) -> str:
        """优先根目录,其次 archive/(用于 read,如历史回看)"""
        p = self._file_path(target_date)
        if os.path.exists(p):
            return p
        p_arc = self._archive_path(target_date)
        if os.path.exists(p_arc):
            return p_arc
        return self._file_path(target_date)  # 不存在时返回根路径

    def load_todos(self, target_date: date) -> List[TodoItem]:
        """加载指定日期的待办列表(支持 archive/ 历史回看)"""
        filepath = self._resolve_path(target_date)
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

    def ensure_today_file(self, carry_forward: bool = True) -> date:
        """确保今天的文件存在，返回今天的日期。

        若 carry_forward=True 且今天文件首次创建，
        自动把最近一天的未完成项（- [ ]）带过来；
        已完成项（- [x]）留在原文件不动。
        """
        today = date.today()
        filepath = self._file_path(today)
        if os.path.exists(filepath):
            return today  # 已存在，不动

        # 首次创建今天文件 → 尝试 carry forward
        carried = []
        if carry_forward:
            previous_dates = [d for d in self.get_available_dates() if d < today]
            if previous_dates:
                most_recent = max(previous_dates)
                prev_todos = self.load_todos(most_recent)
                # 只带未完成的，重置 created_at 为今天
                for t in prev_todos:
                    if not t.done:
                        t.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        carried.append(t)

        self.save_todos(today, carried)

        # v1.2.0 · carry 完后,把根目录所有 < today 的旧文件移到 archive/
        # 满足 Libo 诉求:第二天主目录干净,昨天完整内容(含 - [x])保留在 archive 留底
        self._archive_old_files(today)

        return today

    def _archive_old_files(self, today: date) -> int:
        """把根目录所有日期 < today 的 .md 文件 move 到 archive/ 子目录。
        返回归档的文件数。已在 archive/ 中的文件不重复处理。
        """
        if not os.path.exists(self.base_dir):
            return 0
        archive_dir = self._archive_dir()
        moved = 0
        for filename in os.listdir(self.base_dir):
            match = re.match(r"^(\d{4}-\d{2}-\d{2})\.md$", filename)
            if not match:
                continue
            try:
                d = datetime.strptime(match.group(1), "%Y-%m-%d").date()
            except ValueError:
                continue
            if d >= today:
                continue
            src = os.path.join(self.base_dir, filename)
            os.makedirs(archive_dir, exist_ok=True)
            dst = os.path.join(archive_dir, filename)
            if os.path.exists(dst):
                # archive 已有同名文件(不应发生),跳过避免覆盖
                continue
            try:
                shutil.move(src, dst)
                moved += 1
            except OSError as e:
                print(f"[DataStore] 归档失败: {src} → {dst}, 错误: {e}")
        return moved

    def merge_carry_forward(self, target_date: date = None) -> int:
        """手动把最近一天的未完成项追加到目标日期文件末尾（去重）。
        返回追加的条数。用于一次性补救：今天文件已存在但缺昨天未完成项。
        """
        if target_date is None:
            target_date = date.today()

        existing = self.load_todos(target_date)
        existing_texts = {t.text for t in existing}

        previous_dates = [d for d in self.get_available_dates() if d < target_date]
        if not previous_dates:
            return 0

        most_recent = max(previous_dates)
        prev_todos = self.load_todos(most_recent)

        carried = []
        for t in prev_todos:
            if t.done:
                continue
            if t.text in existing_texts:
                continue  # 去重
            t.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            carried.append(t)

        if carried:
            self.save_todos(target_date, existing + carried)
        return len(carried)

    def get_available_dates(self) -> List[date]:
        """获取所有有记录的日期列表(扫根目录 + archive/)"""
        dates = set()
        if not os.path.exists(self.base_dir):
            return []

        for scan_dir in [self.base_dir, self._archive_dir()]:
            if not os.path.exists(scan_dir):
                continue
            for filename in os.listdir(scan_dir):
                match = re.match(r"^(\d{4}-\d{2}-\d{2})\.md$", filename)
                if match:
                    try:
                        d = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                        dates.add(d)
                    except ValueError:
                        continue

        return sorted(dates, reverse=True)

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
