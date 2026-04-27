"""
config.py — 配置管理
负责读写 config.json（窗口位置、数据路径等）
"""

import json
import os
import sys
from typing import Optional


def get_app_dir() -> str:
    """获取应用所在目录（exe 或 py 文件所在目录）"""
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后
        return os.path.dirname(sys.executable)
    else:
        # 开发模式
        return os.path.dirname(os.path.abspath(__file__))


DEFAULT_CONFIG = {
    # 数据存储路径（默认放用户主目录下的 daily_todo/）
    # Obsidian 用户可改成 vault 内路径，例如 r"F:\YourVault\daily_todo"
    "data_dir": os.path.join(os.path.expanduser("~"), "daily_todo"),
    # 窗口位置（None 表示默认贴右上角）
    "window_x": None,
    "window_y": None,
    # 窗口尺寸
    "window_width": 280,
    "window_height": 460,
    # 透明度（0.0 ~ 1.0）
    "opacity": 0.92,
}


class Config:
    """配置管理器"""

    def __init__(self):
        self.config_path = os.path.join(get_app_dir(), "config.json")
        self.data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        """从 config.json 加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.data.update(saved)
            except Exception as e:
                print(f"[Config] 加载配置失败: {e}")

    def save(self):
        """保存配置到 config.json"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] 保存配置失败: {e}")

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value):
        self.data[key] = value

    @property
    def data_dir(self) -> str:
        return self.data["data_dir"]

    @property
    def window_x(self) -> Optional[int]:
        return self.data.get("window_x")

    @property
    def window_y(self) -> Optional[int]:
        return self.data.get("window_y")

    @property
    def window_width(self) -> int:
        return self.data.get("window_width", 280)

    @property
    def window_height(self) -> int:
        return self.data.get("window_height", 400)

    @property
    def opacity(self) -> float:
        return self.data.get("opacity", 0.92)

    def save_window_position(self, x: int, y: int):
        """保存窗口位置"""
        self.data["window_x"] = x
        self.data["window_y"] = y
        self.save()

    def save_window_size(self, width: int, height: int):
        """保存窗口尺寸"""
        self.data["window_width"] = width
        self.data["window_height"] = height
        self.save()
