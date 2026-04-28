# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
