"""
每日待办 · 桌面便签
====================
极简黑白风格的 Windows 桌面待办应用
数据以 Obsidian 兼容 Markdown 格式存储

启动方式：
  python main.py
  或双击 DailyTodo.exe
"""

import sys
import os
from datetime import date

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from config import Config
from data_store import DataStore
from main_window import MainWindow
from hotkey import HotkeyManager


def main():
    # ─── 初始化 Qt 应用 ───
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，由托盘控制

    # 设置全局字体
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # ─── 加载配置 ───
    config = Config()

    # ─── 确保数据目录存在 ───
    data_dir = config.data_dir
    os.makedirs(data_dir, exist_ok=True)

    # ─── 初始化数据存储 ───
    store = DataStore(data_dir)
    store.ensure_today_file()

    # ─── 创建主窗口 ───
    window = MainWindow(config, store)
    window.show()

    # ─── 注册全局热键 ───
    def on_hotkey():
        """热键回调 — 需要在主线程中执行 UI 操作"""
        QTimer.singleShot(0, window._show_and_focus)

    hotkey_mgr = HotkeyManager(on_hotkey)
    hotkey_mgr.start()

    # ─── 运行事件循环 ───
    exit_code = app.exec()

    # ─── 清理 ───
    hotkey_mgr.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
