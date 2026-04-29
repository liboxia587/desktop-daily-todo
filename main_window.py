"""
main_window.py — 主窗口 UI
淡黄色羊皮纸风格，无边框半透明，红黄蓝优先级标记
"""

import sys
import os
from datetime import date, datetime, timedelta

from PyQt6.QtCore import (
    Qt, QPoint, QTimer, QSize, QDate, pyqtSignal, QRect, QEvent
)
from PyQt6.QtGui import (
    QFont, QColor, QIcon, QAction, QPainter, QPen,
    QCursor, QFontMetrics, QPalette, QPixmap, QBrush
)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea,
    QFrame, QSystemTrayIcon, QMenu, QApplication,
    QCalendarWidget, QDialog, QGraphicsDropShadowEffect,
    QSizePolicy, QSizeGrip, QGridLayout
)

from data_store import (
    DataStore, TodoItem,
    PRIORITY_HIGH, PRIORITY_MID, PRIORITY_LOW, PRIORITY_ORDER
)
from config import Config


# ─── 颜色常量（羊皮纸 v2 · 精致化）─────────────────────────
BG_COLOR = "#FAF1DD"          # 米黄底（更柔和）
BG_HEADER = "#F4E8D0"         # 标题栏（微深）
TEXT_PRIMARY = "#3A2E1F"      # 主文字（深棕，对比更高）
TEXT_SECONDARY = "#9C8A72"    # 次要文字（柔棕灰）
TEXT_DONE = "#C4B59A"         # 已完成（柔和褪色）
ACCENT = "#A87C4A"            # 强调色（古铜）
BORDER_COLOR = "#E8DDC4"      # 边框（几乎隐形）
HOVER_BG = "#EFE3C5"          # hover 暖色微光
INPUT_BG = "#FFF8E6"          # 输入框米白
SCROLLBAR_BG = "#FAF1DD"      # 滚动条背景
SCROLLBAR_HANDLE = "#D4C4A8"  # 滚动条滑块

# 优先级颜色（莫兰迪化，降饱和）
PRIORITY_COLORS = {
    PRIORITY_HIGH: "#C75450",  # 暗红（不刺眼）
    PRIORITY_MID:  "#D99850",  # 琥珀
    PRIORITY_LOW:  "#7D92A8",  # 灰蓝
}

# 心情 emoji 候选（卡通有趣）
MOOD_EMOJIS = [
    "🚀", "💪", "🎯", "⚡",
    "😎", "🥳", "🔥", "✨",
    "☕", "🍵", "🌱", "🐢",
    "😴", "🤔", "🌧️", "🌈",
]
DEFAULT_MOOD = "✨"

# 卡通字型（系统自带 fallback 链）
CARTOON_FONT = "Segoe Print"  # Windows 自带手写卡通体
EMOJI_FONT = "Segoe UI Emoji"


class PriorityDot(QLabel):
    """优先级圆点（可点击切换）"""

    clicked = pyqtSignal()

    def __init__(self, priority: str, clickable: bool = True, parent=None):
        super().__init__(parent)
        self.priority = priority
        self.clickable = clickable
        self.setFixedSize(16, 16)
        if clickable:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_style()

    def set_priority(self, priority: str):
        self.priority = priority
        self._update_style()

    def _update_style(self):
        color = PRIORITY_COLORS.get(self.priority, PRIORITY_COLORS[PRIORITY_MID])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 8px;
                border: none;
            }}
        """)
        # 设置 tooltip
        names = {PRIORITY_HIGH: "高优先", PRIORITY_MID: "中优先", PRIORITY_LOW: "低优先"}
        self.setToolTip(names.get(self.priority, ""))

    def mousePressEvent(self, event):
        if self.clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class TodoItemWidget(QFrame):
    """单条待办项 Widget"""

    toggled = pyqtSignal()
    deleted = pyqtSignal()
    priority_changed = pyqtSignal()

    def __init__(self, item: TodoItem, readonly: bool = False, parent=None):
        super().__init__(parent)
        self.item = item
        self.readonly = readonly
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(30)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor) if not self.readonly
                       else QCursor(Qt.CursorShape.ArrowCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 8, 0)
        layout.setSpacing(8)

        # 优先级圆点
        self.priority_dot = PriorityDot(
            self.item.priority,
            clickable=not self.readonly
        )
        self.priority_dot.clicked.connect(self._on_priority_click)
        layout.addWidget(self.priority_dot)

        # 复选框
        self.checkbox_label = QLabel()
        self.checkbox_label.setFixedSize(18, 18)
        self._update_checkbox()
        layout.addWidget(self.checkbox_label)

        # 文字
        self.text_label = QLabel(self.item.text)
        self.text_label.setFont(QFont("Segoe UI", 10))
        self._update_text_style()
        self.text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.text_label)

        self._update_frame_style(hover=False)

    def _on_priority_click(self):
        """点击优先级圆点 → 循环切换"""
        self.item.cycle_priority()
        self.priority_dot.set_priority(self.item.priority)
        self.priority_changed.emit()

    def _update_checkbox(self):
        if self.item.done:
            self.checkbox_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {TEXT_SECONDARY};
                    border-radius: 9px;
                    border: none;
                }}
            """)
        else:
            self.checkbox_label.setStyleSheet(f"""
                QLabel {{
                    background-color: transparent;
                    border-radius: 9px;
                    border: 2px solid {TEXT_SECONDARY};
                }}
            """)

    def _update_text_style(self):
        if self.item.done:
            self.text_label.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_DONE};
                    text-decoration: line-through;
                    background: transparent;
                }}
            """)
        else:
            self.text_label.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_PRIMARY};
                    background: transparent;
                }}
            """)

    def _update_frame_style(self, hover: bool = False):
        bg = HOVER_BG if hover else "transparent"
        self.setStyleSheet(f"""
            TodoItemWidget {{
                background-color: {bg};
                border: none;
                border-radius: 6px;
            }}
        """)

    def enterEvent(self, event):
        if not self.readonly:
            self._update_frame_style(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_frame_style(hover=False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.readonly:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查点击位置是否在优先级圆点区域（左侧 30px 内）
            if event.position().x() > 30:
                self.item.done = not self.item.done
                self._update_checkbox()
                self._update_text_style()
                self.toggled.emit()
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        if self.readonly:
            return
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {BG_COLOR};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {HOVER_BG};
            }}
        """)
        delete_action = menu.addAction("删除")
        action = menu.exec(event.globalPos())
        if action == delete_action:
            self.deleted.emit()


class HistoryDialog(QDialog):
    """历史回看日历对话框"""

    date_selected = pyqtSignal(QDate)

    def __init__(self, available_dates: list, parent=None):
        super().__init__(parent)
        self.available_dates = set(available_dates)
        self.setWindowTitle("选择日期")
        self.setFixedSize(320, 300)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)

        self.calendar = QCalendarWidget()
        self.calendar.setMaximumDate(QDate.currentDate())
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.calendar.setStyleSheet(f"""
            QCalendarWidget {{
                background-color: {BG_COLOR};
                color: {TEXT_PRIMARY};
                border: none;
            }}
            QCalendarWidget QToolButton {{
                color: {TEXT_PRIMARY};
                background-color: {BG_HEADER};
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {HOVER_BG};
            }}
            QCalendarWidget QMenu {{
                background-color: {BG_COLOR};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
            }}
            QCalendarWidget QSpinBox {{
                background-color: {INPUT_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 3px;
            }}
            QCalendarWidget QAbstractItemView {{
                background-color: {BG_COLOR};
                color: {TEXT_PRIMARY};
                selection-background-color: {BORDER_COLOR};
                selection-color: {ACCENT};
                border: none;
                outline: none;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                color: {TEXT_PRIMARY};
            }}
            QCalendarWidget QAbstractItemView:disabled {{
                color: {TEXT_DONE};
            }}
        """)

        self.calendar.clicked.connect(self._on_date_clicked)
        container_layout.addWidget(self.calendar)

        layout.addWidget(container)

    def _on_date_clicked(self, qdate: QDate):
        self.date_selected.emit(qdate)
        self.accept()


class MoodPickerDialog(QDialog):
    """心情 emoji 4×4 网格选择器"""

    mood_selected = pyqtSignal(str)

    def __init__(self, current_mood: str = "", parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._setup_ui(current_mood)

    def _setup_ui(self, current: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
            }}
        """)
        cl = QVBoxLayout(container)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(8)

        title = QLabel("今天什么心情？")
        title.setFont(QFont(CARTOON_FONT, 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        cl.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(4)
        for i, emoji in enumerate(MOOD_EMOJIS):
            btn = QPushButton(emoji)
            btn.setFixedSize(38, 38)
            btn.setFont(QFont(EMOJI_FONT, 16))
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            is_current = (emoji == current)
            border = f"2px solid {ACCENT}" if is_current else "1px solid transparent"
            bg = HOVER_BG if is_current else "transparent"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    border: {border};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background-color: {HOVER_BG};
                }}
            """)
            btn.clicked.connect(lambda checked=False, e=emoji: self._select(e))
            grid.addWidget(btn, i // 4, i % 4)
        cl.addLayout(grid)

        clear_btn = QPushButton("清除")
        clear_btn.setFixedHeight(24)
        clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: {TEXT_SECONDARY};
                background: transparent;
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {HOVER_BG};
                color: {TEXT_PRIMARY};
            }}
        """)
        clear_btn.clicked.connect(lambda: self._select(""))
        cl.addWidget(clear_btn)

        layout.addWidget(container)

        self.setFixedSize(196, 220)

    def _select(self, emoji: str):
        self.mood_selected.emit(emoji)
        self.accept()


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, config: Config, data_store: DataStore):
        super().__init__()
        self.config = config
        self.data_store = data_store
        self.current_date = date.today()
        self.todos = []
        self.is_viewing_history = False
        self._drag_pos = None
        self._midnight_timer = None

        # 心情抬头状态
        self.current_mood = ""
        self.current_slogan = ""

        # v1.2.0 · 边缘 resize 状态
        self._resize_edge = None
        self._resize_start_global = None
        self._resize_start_geom = None

        self._setup_window()
        self._setup_ui()
        self._setup_tray()
        self._setup_midnight_timer()
        self._load_data()

        # v1.2.0 · 装边缘 resize 监听(必须在 UI 建好之后)
        QTimer.singleShot(0, self._install_edge_resize)

    def _setup_window(self):
        """配置窗口属性"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Tool 窗口不抢焦点
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(self.config.opacity)

        # 恢复位置或默认贴右上角
        width = self.config.window_width
        height = self.config.window_height

        # 计算"主屏右上角"作为安全默认位置
        primary = QApplication.primaryScreen()
        if primary:
            pg = primary.availableGeometry()
            default_x = pg.right() - width - 20
            default_y = pg.top() + 20
        else:
            default_x, default_y = 100, 100

        # 校验保存的位置是否仍在某个真实屏幕的可见范围内
        # （防止外接副屏断开后，窗口飞到不存在的虚拟屏幕坐标 → 看不见）
        saved_x = self.config.window_x
        saved_y = self.config.window_y
        position_valid = False
        if saved_x is not None and saved_y is not None:
            for s in QApplication.screens():
                geo = s.availableGeometry()
                # 至少要能看到窗口左上角的标题栏区域（>= 60px 在屏内）
                if (geo.left() - 50 <= saved_x <= geo.right() - 60
                        and geo.top() - 10 <= saved_y <= geo.bottom() - 60):
                    position_valid = True
                    break

        if position_valid:
            self.setGeometry(saved_x, saved_y, width, height)
        else:
            self.setGeometry(default_x, default_y, width, height)
            # 顺手把无效位置擦掉，下次启动直接走默认（防止 config.json 里残留脏数据）
            if saved_x is not None or saved_y is not None:
                self.config.set("window_x", None)
                self.config.set("window_y", None)
                self.config.save()

        self.setMinimumSize(240, 300)

    def _setup_ui(self):
        """构建 UI"""
        # 主容器
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 外层容器（带圆角背景）
        self.outer_frame = QFrame()
        self.outer_frame.setObjectName("outerFrame")
        self.outer_frame.setStyleSheet(f"""
            #outerFrame {{
                background-color: {BG_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
            }}
        """)
        outer_layout = QVBoxLayout(self.outer_frame)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ─── 标题栏 ───
        self._build_header(outer_layout)

        # ─── 心情抬头（emoji + slogan）───
        self._build_mood_bar(outer_layout)

        # ─── 分隔线 ───
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {BORDER_COLOR};")
        outer_layout.addWidget(separator)

        # ─── 待办列表区 ───
        self._build_todo_list(outer_layout)

        # ─── 输入框 ───
        self._build_input(outer_layout)

        # ─── 底部状态栏 ───
        self._build_footer(outer_layout)

        main_layout.addWidget(self.outer_frame)

    def _build_header(self, parent_layout):
        """构建标题栏"""
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_HEADER};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border: none;
            }}
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 8, 8, 8)
        header_layout.setSpacing(4)

        # 日期按钮（可点击查看历史）
        self.date_btn = QPushButton()
        self.date_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.date_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.date_btn.setStyleSheet(f"""
            QPushButton {{
                color: {TEXT_PRIMARY};
                background: transparent;
                border: none;
                text-align: left;
                padding: 2px 4px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {HOVER_BG};
            }}
        """)
        self.date_btn.clicked.connect(self._show_calendar)
        header_layout.addWidget(self.date_btn)

        header_layout.addStretch()

        # 返回今天按钮（仅历史模式显示）
        self.back_btn = QPushButton("今天")
        self.back_btn.setFont(QFont("Segoe UI", 9))
        self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_btn.setFixedHeight(26)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                color: {TEXT_SECONDARY};
                background-color: {BG_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 13px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {BORDER_COLOR};
                color: {TEXT_PRIMARY};
            }}
        """)
        self.back_btn.clicked.connect(self._back_to_today)
        self.back_btn.setVisible(False)
        header_layout.addWidget(self.back_btn)

        # 最小化到托盘按钮
        minimize_btn = QPushButton("—")
        minimize_btn.setFont(QFont("Segoe UI", 12))
        minimize_btn.setFixedSize(28, 28)
        minimize_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        minimize_btn.setStyleSheet(f"""
            QPushButton {{
                color: {TEXT_SECONDARY};
                background: transparent;
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: {HOVER_BG};
                color: {TEXT_PRIMARY};
            }}
        """)
        minimize_btn.clicked.connect(self._minimize_to_tray)
        header_layout.addWidget(minimize_btn)

        parent_layout.addWidget(header)

        # 标题栏可拖动
        header.mousePressEvent = self._header_mouse_press
        header.mouseMoveEvent = self._header_mouse_move
        header.mouseReleaseEvent = self._header_mouse_release

    def _build_mood_bar(self, parent_layout):
        """构建心情抬头：emoji 按钮 + slogan 输入"""
        bar = QFrame()
        bar.setFixedHeight(44)
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_HEADER};
                border: none;
            }}
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(10, 4, 10, 4)
        bar_layout.setSpacing(8)

        # 心情 emoji 按钮（点击弹出选择器）
        self.mood_btn = QPushButton(DEFAULT_MOOD)
        self.mood_btn.setFixedSize(36, 36)
        self.mood_btn.setFont(QFont(EMOJI_FONT, 18))
        self.mood_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mood_btn.setToolTip("点我选今天的心情")
        self.mood_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1.5px dashed {BORDER_COLOR};
                border-radius: 18px;
            }}
            QPushButton:hover {{
                background-color: {HOVER_BG};
                border-style: solid;
                border-color: {ACCENT};
            }}
        """)
        self.mood_btn.clicked.connect(self._show_mood_picker)
        bar_layout.addWidget(self.mood_btn)

        # slogan 输入（卡通字型）
        self.slogan_input = QLineEdit()
        self.slogan_input.setPlaceholderText("写一句今天的口号...")
        self.slogan_input.setFont(QFont(CARTOON_FONT, 11))
        self.slogan_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {TEXT_PRIMARY};
                border: none;
                border-bottom: 1px dashed {BORDER_COLOR};
                padding: 4px 2px;
                font-style: italic;
            }}
            QLineEdit:focus {{
                border-bottom: 1.5px solid {ACCENT};
            }}
            QLineEdit::placeholder {{
                color: {TEXT_DONE};
            }}
        """)
        self.slogan_input.editingFinished.connect(self._on_slogan_changed)
        bar_layout.addWidget(self.slogan_input, 1)

        parent_layout.addWidget(bar)

    def _show_mood_picker(self):
        """弹出心情 emoji 选择器"""
        dialog = MoodPickerDialog(self.current_mood, self)
        # 定位在 mood 按钮下方
        btn_pos = self.mood_btn.mapToGlobal(QPoint(0, self.mood_btn.height() + 4))
        dialog.move(btn_pos)
        dialog.mood_selected.connect(self._on_mood_selected)
        dialog.exec()

    def _on_mood_selected(self, emoji: str):
        """选择心情后保存"""
        if self.is_viewing_history:
            return
        self.current_mood = emoji
        self._update_mood_display()
        self._save_metadata()

    def _on_slogan_changed(self):
        """slogan 编辑完成（失去焦点或回车）后保存"""
        if self.is_viewing_history:
            return
        new_slogan = self.slogan_input.text().strip()
        if new_slogan != self.current_slogan:
            self.current_slogan = new_slogan
            self._save_metadata()

    def _update_mood_display(self):
        """更新 emoji 按钮显示"""
        display = self.current_mood if self.current_mood else DEFAULT_MOOD
        self.mood_btn.setText(display)
        # 已设心情时去掉虚线、变实线
        if self.current_mood:
            self.mood_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {HOVER_BG};
                    border: 1.5px solid {ACCENT};
                    border-radius: 18px;
                }}
                QPushButton:hover {{
                    background-color: {BORDER_COLOR};
                }}
            """)
        else:
            self.mood_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1.5px dashed {BORDER_COLOR};
                    border-radius: 18px;
                }}
                QPushButton:hover {{
                    background-color: {HOVER_BG};
                    border-style: solid;
                    border-color: {ACCENT};
                }}
            """)

    def _save_metadata(self):
        """单独保存 mood/slogan（重写整个文件）"""
        if self.is_viewing_history:
            return
        self.data_store.save_todos(
            self.current_date, self.todos,
            mood=self.current_mood,
            slogan=self.current_slogan
        )

    def _build_todo_list(self, parent_layout):
        """构建待办列表滚动区域"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {BG_COLOR};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {SCROLLBAR_BG};
                width: 6px;
                margin: 0;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {SCROLLBAR_HANDLE};
                min-height: 30px;
                border-radius: 3px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self.todo_container = QWidget()
        self.todo_container.setStyleSheet(f"background-color: {BG_COLOR};")
        self.todo_layout = QVBoxLayout(self.todo_container)
        self.todo_layout.setContentsMargins(4, 2, 4, 2)
        self.todo_layout.setSpacing(0)
        self.todo_layout.addStretch()

        self.scroll_area.setWidget(self.todo_container)
        parent_layout.addWidget(self.scroll_area, 1)

    def _build_input(self, parent_layout):
        """构建输入框"""
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_COLOR};
                border: none;
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 6, 12, 6)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("添加新待办，回车确认...")
        self.input_field.setFont(QFont("Segoe UI", 10))
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {INPUT_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 8px 12px;
                selection-background-color: {BORDER_COLOR};
            }}
            QLineEdit:focus {{
                border-color: {TEXT_SECONDARY};
            }}
            QLineEdit::placeholder {{
                color: {TEXT_DONE};
            }}
        """)
        self.input_field.returnPressed.connect(self._add_todo)
        input_layout.addWidget(self.input_field)

        parent_layout.addWidget(input_frame)

    def _build_footer(self, parent_layout):
        """构建底部状态栏"""
        footer = QFrame()
        footer.setFixedHeight(28)
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_HEADER};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
                border: none;
            }}
        """)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(14, 0, 14, 0)

        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Segoe UI", 8))
        self.stats_label.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        footer_layout.addWidget(self.stats_label)

        footer_layout.addStretch()

        # 优先级图例
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(3)
        for p, name in [(PRIORITY_HIGH, "高"), (PRIORITY_MID, "中"), (PRIORITY_LOW, "低")]:
            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"""
                QLabel {{
                    background-color: {PRIORITY_COLORS[p]};
                    border-radius: 4px;
                }}
            """)
            legend_layout.addWidget(dot)
            lbl = QLabel(name)
            lbl.setFont(QFont("Segoe UI", 7))
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
            legend_layout.addWidget(lbl)

        footer_layout.addLayout(legend_layout)

        # 间隔
        spacer = QLabel("  ")
        spacer.setStyleSheet("background: transparent;")
        footer_layout.addWidget(spacer)

        # 快捷键提示
        hotkey_label = QLabel("Ctrl+Alt+N")
        hotkey_label.setFont(QFont("Segoe UI", 7))
        hotkey_label.setStyleSheet(f"color: {TEXT_DONE}; background: transparent;")
        footer_layout.addWidget(hotkey_label)

        parent_layout.addWidget(footer)

    # ─── 系统托盘 ───────────────────────────────────────

    def _setup_tray(self):
        """设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)

        # 创建托盘图标（暖色调）
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("transparent"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(BG_HEADER))
        painter.drawRoundedRect(2, 2, 28, 28, 4, 4)
        painter.setPen(QPen(QColor(TEXT_PRIMARY), 2))
        painter.drawLine(8, 11, 24, 11)
        painter.drawLine(8, 16, 24, 16)
        painter.drawLine(8, 21, 20, 21)
        # 小红点
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(PRIORITY_COLORS[PRIORITY_HIGH]))
        painter.drawEllipse(22, 6, 6, 6)
        painter.end()

        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)
        self.tray_icon.setToolTip("每日待办")

        # 托盘菜单
        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {BG_COLOR};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {HOVER_BG};
            }}
        """)

        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self._show_window)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    # ─── 午夜定时器 ───────────────────────────────────────

    def _setup_midnight_timer(self):
        """设置午夜自动切换定时器"""
        self._midnight_timer = QTimer(self)
        self._midnight_timer.timeout.connect(self._check_date_change)
        self._midnight_timer.start(30000)  # 每 30 秒检查一次

    def _check_date_change(self):
        """检查是否跨天"""
        today = date.today()
        if today != self.current_date and not self.is_viewing_history:
            self.current_date = today
            self.data_store.ensure_today_file()
            self._load_data()

    # ─── 数据操作 ───────────────────────────────────────

    def _load_data(self):
        """加载当前日期的数据"""
        self.todos = self.data_store.load_todos(self.current_date)
        # 加载心情与口号
        meta = self.data_store.load_metadata(self.current_date)
        self.current_mood = meta.get("mood", "")
        self.current_slogan = meta.get("slogan", "")
        self._refresh_ui()

    def _save_data(self):
        """保存当前数据（连同 mood/slogan 一起）"""
        if not self.is_viewing_history:
            self.data_store.save_todos(
                self.current_date, self.todos,
                mood=self.current_mood,
                slogan=self.current_slogan,
            )
        self._update_stats()

    def _add_todo(self):
        """添加新待办"""
        if self.is_viewing_history:
            return

        text = self.input_field.text().strip()
        if not text:
            return

        item = TodoItem(text=text)  # 默认黄色（mid）优先级
        self.todos.append(item)
        self.input_field.clear()
        self._save_data()
        self._refresh_todo_list()

        # 滚动到底部
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def _toggle_todo(self, index: int):
        """切换待办完成状态"""
        if 0 <= index < len(self.todos):
            self._save_data()

    def _change_priority(self, index: int):
        """更改优先级"""
        if 0 <= index < len(self.todos):
            self._save_data()

    def _delete_todo(self, index: int):
        """删除待办"""
        if 0 <= index < len(self.todos):
            self.todos.pop(index)
            self._save_data()
            self._refresh_todo_list()

    # ─── UI 刷新 ───────────────────────────────────────

    def _refresh_ui(self):
        """刷新整个 UI"""
        self._update_date_display()
        self._refresh_todo_list()
        self._update_stats()

        # 心情抬头同步
        self._update_mood_display()
        # blockSignals 防止 setText 触发 editingFinished 死循环
        self.slogan_input.blockSignals(True)
        self.slogan_input.setText(self.current_slogan)
        self.slogan_input.blockSignals(False)

        # 历史模式下隐藏输入区，slogan/mood 变只读
        self.input_field.setVisible(not self.is_viewing_history)
        self.back_btn.setVisible(self.is_viewing_history)
        self.slogan_input.setReadOnly(self.is_viewing_history)
        self.mood_btn.setEnabled(not self.is_viewing_history)

    def _update_date_display(self):
        """更新日期显示"""
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekdays[self.current_date.weekday()]

        if self.current_date == date.today():
            self.date_btn.setText(f"{self.current_date.strftime('%m月%d日')} {weekday}")
        else:
            self.date_btn.setText(f"📅 {self.current_date.strftime('%Y-%m-%d')} {weekday}")

    def _refresh_todo_list(self):
        """刷新待办列表"""
        # 清空现有项
        while self.todo_layout.count() > 1:  # 保留最后的 stretch
            child = self.todo_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 添加待办项
        for i, item in enumerate(self.todos):
            widget = TodoItemWidget(item, readonly=self.is_viewing_history)
            widget.toggled.connect(lambda idx=i: self._toggle_todo(idx))
            widget.deleted.connect(lambda idx=i: self._delete_todo(idx))
            widget.priority_changed.connect(lambda idx=i: self._change_priority(idx))
            self.todo_layout.insertWidget(self.todo_layout.count() - 1, widget)

        # 空状态提示
        if not self.todos:
            empty_label = QLabel("暂无待办" if not self.is_viewing_history else "当天无记录")
            empty_label.setFont(QFont("Segoe UI", 10))
            empty_label.setStyleSheet(f"color: {TEXT_DONE}; background: transparent;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.todo_layout.insertWidget(0, empty_label)

    def _update_stats(self):
        """更新统计信息"""
        done, total = self.data_store.get_week_stats(self.current_date)
        if total > 0:
            pct = int(done / total * 100)
            self.stats_label.setText(f"本周 {done}/{total} ({pct}%)")
        else:
            self.stats_label.setText("本周暂无待办")

    # ─── 日历 / 历史 ───────────────────────────────────────

    def _show_calendar(self):
        """显示日历选择器"""
        available = self.data_store.get_available_dates()
        dialog = HistoryDialog(available, self)

        # 定位在日期按钮下方
        btn_pos = self.date_btn.mapToGlobal(QPoint(0, self.date_btn.height()))
        dialog.move(btn_pos)

        dialog.date_selected.connect(self._on_history_date_selected)
        dialog.exec()

    def _on_history_date_selected(self, qdate: QDate):
        """选择历史日期"""
        selected = date(qdate.year(), qdate.month(), qdate.day())
        if selected == date.today():
            self._back_to_today()
        else:
            self.current_date = selected
            self.is_viewing_history = True
            self._load_data()

    def _back_to_today(self):
        """返回今天"""
        self.current_date = date.today()
        self.is_viewing_history = False
        self.data_store.ensure_today_file()
        self._load_data()

    # ─── v1.2.0 · 边缘 resize ─────────────────────────────

    _RESIZE_MARGIN = 8
    _CURSOR_MAP = {
        'l': Qt.CursorShape.SizeHorCursor, 'r': Qt.CursorShape.SizeHorCursor,
        't': Qt.CursorShape.SizeVerCursor, 'b': Qt.CursorShape.SizeVerCursor,
        'tl': Qt.CursorShape.SizeFDiagCursor, 'br': Qt.CursorShape.SizeFDiagCursor,
        'tr': Qt.CursorShape.SizeBDiagCursor, 'bl': Qt.CursorShape.SizeBDiagCursor,
    }

    def _install_edge_resize(self):
        """安装 event filter 到所有 child widgets,使边缘 resize 跨子组件生效"""
        self.setMouseTracking(True)
        for w in self.findChildren(QWidget):
            w.setMouseTracking(True)
            w.installEventFilter(self)

    def _check_edge(self, local_pos):
        """局部坐标 → 边缘字符串('l'/'r'/'t'/'b'/'tl'/...) 或 None"""
        x, y, w, h, m = local_pos.x(), local_pos.y(), self.width(), self.height(), self._RESIZE_MARGIN
        on_l, on_r = x <= m, x >= w - m
        on_t, on_b = y <= m, y >= h - m
        if on_t and on_l: return 'tl'
        if on_t and on_r: return 'tr'
        if on_b and on_l: return 'bl'
        if on_b and on_r: return 'br'
        if on_l: return 'l'
        if on_r: return 'r'
        if on_t: return 't'
        if on_b: return 'b'
        return None

    def eventFilter(self, obj, event):
        et = event.type()
        # 只处理鼠标事件
        if et in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
            try:
                gp = event.globalPosition().toPoint()
            except AttributeError:
                return super().eventFilter(obj, event)
            local = self.mapFromGlobal(gp)

            if et == QEvent.Type.MouseMove:
                if self._resize_edge:
                    # 正在 resize → 改 geometry
                    self._do_resize(gp)
                    return True
                elif not event.buttons():
                    # 未按键 → 检测边缘改 cursor
                    edge = self._check_edge(local)
                    if edge:
                        self.setCursor(self._CURSOR_MAP[edge])
                        return False  # 不消费,让 child 也能处理 hover
                    else:
                        self.unsetCursor()

            elif et == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                edge = self._check_edge(local)
                if edge:
                    self._resize_edge = edge
                    self._resize_start_global = gp
                    self._resize_start_geom = self.geometry()
                    return True  # 消费,阻止 child 处理 click

            elif et == QEvent.Type.MouseButtonRelease and self._resize_edge:
                self._resize_edge = None
                self.config.save_window_size(self.width(), self.height())
                self.config.save_window_position(self.x(), self.y())
                self.config.save()
                return True

        return super().eventFilter(obj, event)

    def _do_resize(self, global_pos):
        """根据 edge + 鼠标全局位置 改 geometry"""
        g = self._resize_start_geom
        sp = self._resize_start_global
        dx, dy = global_pos.x() - sp.x(), global_pos.y() - sp.y()
        nx, ny, nw, nh = g.x(), g.y(), g.width(), g.height()
        edge = self._resize_edge
        if 'l' in edge:
            nx, nw = g.x() + dx, g.width() - dx
        elif 'r' in edge:
            nw = g.width() + dx
        if 't' in edge:
            ny, nh = g.y() + dy, g.height() - dy
        elif 'b' in edge:
            nh = g.height() + dy

        # 应用 minimum 限制
        min_w, min_h = self.minimumWidth(), self.minimumHeight()
        if nw < min_w:
            if 'l' in edge:
                nx = g.x() + g.width() - min_w
            nw = min_w
        if nh < min_h:
            if 't' in edge:
                ny = g.y() + g.height() - min_h
            nh = min_h

        self.setGeometry(nx, ny, nw, nh)

    # ─── 窗口拖动 ───────────────────────────────────────

    def _header_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _header_mouse_move(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _header_mouse_release(self, event):
        self._drag_pos = None
        # 保存位置
        pos = self.pos()
        self.config.save_window_position(pos.x(), pos.y())

    # ─── 窗口行为 ───────────────────────────────────────

    def _minimize_to_tray(self):
        """最小化到托盘"""
        self._save_position()
        self.hide()

    def _show_window(self):
        """从托盘恢复显示"""
        self.show()
        self.raise_()
        # 不调用 activateWindow()，避免抢焦点

    def _show_and_focus(self):
        """显示窗口并聚焦到输入框（快捷键调用）"""
        self.show()
        self.raise_()
        self.activateWindow()  # 快捷键唤出时需要激活
        self.input_field.setFocus()

    def _quit_app(self):
        """退出程序"""
        self._save_position()
        self.tray_icon.hide()
        QApplication.quit()

    def _save_position(self):
        """保存窗口位置和尺寸"""
        pos = self.pos()
        size = self.size()
        self.config.save_window_position(pos.x(), pos.y())
        self.config.save_window_size(size.width(), size.height())

    def closeEvent(self, event):
        """重写关闭事件 → 最小化到托盘"""
        event.ignore()
        self._minimize_to_tray()

    def resizeEvent(self, event):
        """窗口大小变化时保存"""
        super().resizeEvent(event)
        # 延迟保存，避免频繁写入
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(lambda: self.config.save_window_size(
            self.size().width(), self.size().height()
        ))
        self._resize_timer.start(500)
