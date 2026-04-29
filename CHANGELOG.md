# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] — 2026-04-29

### Added
- **窗口边缘可拖动改尺寸** ⭐
  - 鼠标放窗口 4 边或 4 角 → 自动变 resize cursor
  - 拖动改宽高,实时响应
  - 关闭/退出时自动保存到 `config.json`,下次启动恢复尺寸
  - 8 px 边缘检测范围,minimum 240×300 防拖到看不见
- **跨天自动归档昨天文件** ⭐
  - 凌晨跨天 carry forward 完成后,把根目录所有 `< today` 的旧 .md 文件 **整文件移到** `daily_todo/archive/`
  - 主目录始终干净:只看到今天.md + archive/ 子目录
  - 已完成项 (`- [x]`) 完整保留在 archive 文件中(留底,不删)
  - 历史日历回看自动扫 archive/,跨天后仍能查任意一天
  - 已 archive 的文件不重复处理(防覆盖)

### Changed
- `DataStore.load_todos()` 增强:优先读根目录,其次 archive/(用于历史回看)
- `DataStore.get_available_dates()` 增强:扫两处合并去重排序

### Internal
- 数据格式向后兼容,v1.0.x / v1.1.x 写的 `.md` 文件可直接被 v1.2.0 读取
- 严格遵守 [AGENT.md 第七节第 4 条] 不删除任何文件原则:已完成项随昨天文件 archive 留底,**绝无物理删除**

---

## [1.1.0] — 2026-04-28

### Added
- **跨天自动 Carry Forward 未完成项** ⭐
  - 凌晨跨天时，今天文件首次创建会自动把"最近一天的未完成 task（`- [ ]`）"复制过来
  - 已完成项（`- [x]`）留在原文件不动，作为日记 / 复盘留底
  - 优先级标签（`#p/high` / `#p/mid` / `#p/low`）一并保留
  - 按文本去重（防止你今天手动加了同名 task 后被重复带入）
  - 新增公共方法 `DataStore.merge_carry_forward()` 用于一次性补救（万一今天文件已存在但缺昨天未完成项时手动调用）
  - `DataStore.ensure_today_file(carry_forward=True)` 默认开启此行为，可设 `False` 关闭

### Fixed
- **窗口位置越界自我修复**(双屏/外接屏断开后窗口"消失")
  - 启动时校验 `config.json` 里保存的 `window_x` / `window_y` 是否仍落在某个真实屏幕范围内
  - 若不在(例如你之前接过外接屏并把便签拖过去,后来副屏断开)→ 自动重置到主屏右上角并清空脏坐标
  - 修复"App 在跑(进程存在)但屏幕完全找不到"的诡异问题

### Internal
- 数据格式向后兼容,v1.0.x 写的 `.md` 文件可直接被 v1.1.0 读取

---

## [1.0.0] — 2026-04-27

### Added
- 首次正式发布
- 按天 markdown 文件存储（YYYY-MM-DD.md + frontmatter date / done / mood / slogan / tags）
- 心情抬头(4×4 emoji 网格 + 卡通字型 slogan 输入)
- 三档优先级(红 / 琥珀 / 灰蓝,莫兰迪降饱和)
- 全局热键 `Ctrl + Alt + N` 唤出
- 历史日历回看 / 跨天自动归档(空文件)/ 系统托盘最小化
- 羊皮纸 v2 视觉(米黄底 #FAF1DD + 古铜强调 #A87C4A + 半透明圆角)
- PyInstaller 单文件 EXE(36 MB,任何人下载双击即用)
- LICENSE: MIT
