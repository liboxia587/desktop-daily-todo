"""
hotkey.py — 全局热键管理
使用 pynput 实现 Ctrl+Alt+N 全局热键

v1.3.1 修复: pynput 在窗口切换 / 输入法切换时可能漏收 release 事件,
导致 modifier 卡在 "_pressed_keys" 里 → 单按 'n' 也触发 callback → 焦点抢到便签。
修法: 触发 n 时用 Win32 GetAsyncKeyState 二次验证 modifier 真的物理按着。
"""

import threading
import sys
import ctypes


def _modifier_physically_down() -> bool:
    """v1.3.1 · 用 Win32 GetAsyncKeyState 验证 Ctrl + Alt 当前物理按着。
    返回 True 仅当 Ctrl(L 或 R) AND Alt(L 或 R) 都真的物理按下。
    """
    if sys.platform != "win32":
        return True  # 非 Win 平台不验证(暂时)
    try:
        # VK 码: VK_CONTROL=0x11, VK_MENU(Alt)=0x12, VK_LCONTROL=0xA2, VK_RCONTROL=0xA3, VK_LMENU=0xA4, VK_RMENU=0xA5
        gks = ctypes.windll.user32.GetAsyncKeyState
        # 高位被设 = 当前物理按下
        def down(vk):
            return (gks(vk) & 0x8000) != 0
        ctrl_down = down(0x11) or down(0xA2) or down(0xA3)
        alt_down = down(0x12) or down(0xA4) or down(0xA5)
        return ctrl_down and alt_down
    except Exception:
        return True  # 调用失败时不阻止(降级到原行为)


class HotkeyManager:
    """全局热键管理器"""

    def __init__(self, callback):
        """
        callback: 热键触发时调用的函数(在主线程中执行)
        """
        self.callback = callback
        self._listener = None
        self._pressed_keys = set()

    def start(self):
        """启动热键监听(在后台线程中运行)"""
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
                # 也检查 vk 码(有些键盘布局下 char 可能为 None)
                if not n_key:
                    try:
                        if hasattr(key, 'vk') and key.vk == 78:  # N 的 vk 码
                            n_key = True
                    except AttributeError:
                        pass

                if ctrl and alt and n_key:
                    # v1.3.1 · 二次验证: modifier 真的物理按着才触发
                    # 防止 pynput 漏收 release 事件 → modifier 卡在 set 里 → 单按 n 被误触
                    if _modifier_physically_down():
                        self.callback()
                    else:
                        # 漏收过 release,清理脏状态
                        for mod in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                                    keyboard.Key.alt_l, keyboard.Key.alt_r]:
                            self._pressed_keys.discard(mod)

            def on_release(key):
                self._pressed_keys.discard(key)

            self._listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            )
            self._listener.daemon = True
            self._listener.start()
            print("[HotkeyManager] 全局热键 Ctrl+Alt+N 已注册(v1.3.1 + Win32 modifier 二次验证)")

        except ImportError:
            print("[HotkeyManager] pynput 未安装,全局热键不可用")
        except Exception as e:
            print(f"[HotkeyManager] 热键注册失败: {e}")

    def stop(self):
        """停止热键监听"""
        if self._listener:
            self._listener.stop()
            self._listener = None
