"""
hotkey.py — 全局热键管理
使用 pynput 实现 Ctrl+Alt+N 全局热键
"""

import threading
import sys


class HotkeyManager:
    """全局热键管理器"""

    def __init__(self, callback):
        """
        callback: 热键触发时调用的函数（在主线程中执行）
        """
        self.callback = callback
        self._listener = None
        self._pressed_keys = set()

    def start(self):
        """启动热键监听（在后台线程中运行）"""
        if sys.platform != "win32":
            print("[HotkeyManager] 全局热键仅支持 Windows 平台")
            return

        try:
            from pynput import keyboard

            def on_press(key):
                self._pressed_keys.add(key)
                # 检查 Ctrl+Alt+N
                ctrl = (
                    keyboard.Key.ctrl_l in self._pressed_keys or
                    keyboard.Key.ctrl_r in self._pressed_keys
                )
                alt = (
                    keyboard.Key.alt_l in self._pressed_keys or
                    keyboard.Key.alt_r in self._pressed_keys
                )
                n_key = False
                try:
                    if hasattr(key, 'char') and key.char and key.char.lower() == 'n':
                        n_key = True
                except AttributeError:
                    pass
                # 也检查 vk 码（有些键盘布局下 char 可能为 None）
                if not n_key:
                    try:
                        if hasattr(key, 'vk') and key.vk == 78:  # N 的 vk 码
                            n_key = True
                    except AttributeError:
                        pass

                if ctrl and alt and n_key:
                    self.callback()

            def on_release(key):
                self._pressed_keys.discard(key)

            self._listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            )
            self._listener.daemon = True
            self._listener.start()
            print("[HotkeyManager] 全局热键 Ctrl+Alt+N 已注册")

        except ImportError:
            print("[HotkeyManager] pynput 未安装，全局热键不可用")
        except Exception as e:
            print(f"[HotkeyManager] 热键注册失败: {e}")

    def stop(self):
        """停止热键监听"""
        if self._listener:
            self._listener.stop()
            self._listener = None
