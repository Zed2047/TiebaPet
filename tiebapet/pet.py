"""黄豆桌宠主窗口。"""

from __future__ import annotations

import random
from dataclasses import replace
from time import monotonic
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QUrl,
    QSequentialAnimationGroup,
    Qt,
    QTimer,
)
from PySide6.QtGui import QAction, QContextMenuEvent, QDesktopServices, QMouseEvent
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QMenu, QMessageBox, QWidget

from .assets import SpriteAtlas
from .autostart import set_autostart
from .config import ConfigManager, PetSettings
from .phrases import PhraseRepository
from .paths import ensure_user_directories, user_data_root
from .settings_dialog import SettingsDialog
from .state import PetState, StateMachine

if TYPE_CHECKING:
    from .plugins.manager import PluginManager


class PetWindow(QWidget):
    """透明、可拖拽、可配置并支持插件的黄豆窗口。"""

    WIDTH = 250
    MIN_HEIGHT = 230
    SPRITE_Y = 92

    def __init__(
        self,
        atlas: SpriteAtlas,
        config_manager: ConfigManager | None = None,
        phrases: PhraseRepository | None = None,
        state_machine: StateMachine | None = None,
    ) -> None:
        super().__init__()
        self.atlas = atlas
        self.config_manager = config_manager or ConfigManager()
        self.settings = self.config_manager.settings
        self.phrases = phrases or PhraseRepository()
        self.state_machine = state_machine or StateMachine()
        self.plugin_manager: PluginManager | None = None

        self.expression = "微微一笑"
        self.auto_wander = self.settings.auto_wander
        self.always_on_top = self.settings.always_on_top
        self._dragging = False
        self._drag_moved = False
        self._drag_announced = False
        self._drag_offset = QPoint()
        self._placed_once = False
        self._last_activity = monotonic()
        self._move_animation: QPropertyAnimation | None = None
        self._sprite_animation: QSequentialAnimationGroup | None = None

        self.setWindowTitle("黄豆")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self._apply_window_flags()

        self.bubble = QLabel(self)
        self.bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bubble.setWordWrap(True)
        self.bubble.hide()

        self.sprite = QLabel(self)
        self.sprite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._refresh_appearance()
        self.set_expression(self.expression, animate=False)

        self._bubble_timer = QTimer(self)
        self._bubble_timer.setSingleShot(True)
        self._bubble_timer.timeout.connect(self.bubble.hide)

        self._behavior_timer = QTimer(self)
        self._behavior_timer.timeout.connect(self._choose_behavior)
        self._update_behavior_timer()
        self._behavior_timer.start()

    def set_plugin_manager(self, manager: PluginManager) -> None:
        self.plugin_manager = manager

    def _apply_window_flags(self) -> None:
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _refresh_appearance(self) -> None:
        sprite_y = max(self.SPRITE_Y, self.settings.bubble_height + 10)
        width = max(self.WIDTH, self.settings.sprite_size + 40)
        height = max(self.MIN_HEIGHT, sprite_y + self.settings.sprite_size + 8)
        self.setFixedSize(width, height)
        self.bubble.setGeometry(8, 5, width - 20, self.settings.bubble_height)
        self.bubble.setStyleSheet(
            "QLabel {"
            " background: rgba(255, 251, 225, 242);"
            " color: #3b2b16;"
            " border: 2px solid #e6b94f;"
            " border-radius: 14px;"
            " padding: 7px 10px;"
            " font-family: 'Microsoft YaHei UI';"
            f" font-size: {self.settings.font_size}px;"
            " font-weight: 600;"
            "}"
        )
        self._reset_sprite_geometry()

    def _update_behavior_timer(self) -> None:
        self._behavior_timer.setInterval(self.settings.behavior_interval_seconds * 1000)

    def showEvent(self, event) -> None:  # noqa: N802 - Qt 接口命名
        super().showEvent(event)
        if self._placed_once:
            return
        self._placed_once = True
        x = self.settings.position_x
        y = self.settings.position_y
        candidate = QPoint(x, y) if x is not None and y is not None else None
        screen = QApplication.screenAt(candidate) if candidate else QApplication.primaryScreen()
        screen = screen or QApplication.primaryScreen()
        if not screen:
            return
        area = screen.availableGeometry()
        if candidate:
            safe_x = min(max(candidate.x(), area.left()), area.right() - self.width() + 1)
            safe_y = min(max(candidate.y(), area.top()), area.bottom() - self.height() + 1)
            self.move(safe_x, safe_y)
        else:
            self.move(area.right() - self.width() - 24, area.bottom() - self.height() - 24)

    def _reset_sprite_geometry(self) -> None:
        x = (self.width() - self.settings.sprite_size) // 2
        y = max(self.SPRITE_Y, self.settings.bubble_height + 10)
        self.sprite.setGeometry(x, y, self.settings.sprite_size, self.settings.sprite_size)

    def set_expression(self, name: str, animate: bool = True) -> None:
        if name not in self.atlas.names:
            return
        self.expression = name
        self._reset_sprite_geometry()
        self.sprite.setPixmap(self.atlas.pixmap(name, self.settings.sprite_size))
        self.setWindowTitle(f"黄豆 - {name}")
        if animate:
            self._animate_sprite(name)

    def react(self, expression: str | None = None) -> None:
        self._touch()
        name = expression or random.choice(self.atlas.names)
        self.set_expression(name)
        self.say(self.phrases.for_expression(name))

    def say(self, text: str, duration_ms: int = 3200) -> None:
        self.bubble.setText(text)
        self.bubble.show()
        self.bubble.raise_()
        self._bubble_timer.start(duration_ms)

    def _touch(self) -> None:
        self._last_activity = monotonic()
        if self.state_machine.current == PetState.SLEEPING:
            self.state_machine.set(PetState.IDLE)

    def _animate_sprite(self, name: str) -> None:
        if self._sprite_animation:
            self._sprite_animation.stop()
        self._reset_sprite_geometry()
        origin = self.sprite.pos()
        group = QSequentialAnimationGroup(self)

        if name in {
            "欢呼", "开心", "兴奋", "笑", "爱", "真棒",
            "黑头高兴", "嘿嘿嘿", "嘻嘻",
        }:
            points = (origin + QPoint(0, -20), origin)
            duration = 150
        elif name in {
            "生气", "喷水", "吐了", "汗", "流汗", "狂汗",
            "紧张", "what", "啊", "泪", "呀咩爹", "喝酒",
        }:
            points = (
                origin + QPoint(-8, 0), origin + QPoint(8, 0),
                origin + QPoint(-6, 0), origin + QPoint(6, 0), origin,
            )
            duration = 65
        else:
            points = (origin + QPoint(-7, -3), origin + QPoint(7, 0), origin)
            duration = 120

        current = origin
        for point in points:
            animation = QPropertyAnimation(self.sprite, b"pos", group)
            animation.setStartValue(current)
            animation.setEndValue(point)
            animation.setDuration(duration)
            animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            group.addAnimation(animation)
            current = point
        group.finished.connect(self._reset_sprite_geometry)
        self._sprite_animation = group
        group.start()

    def _choose_behavior(self) -> None:
        if self._dragging or not self.isVisible():
            return
        if self.state_machine.current in {
            PetState.WORKING,
            PetState.REMINDING,
            PetState.DRAGGING,
        }:
            return
        inactive_seconds = monotonic() - self._last_activity
        if inactive_seconds >= self.settings.sleep_after_minutes * 60:
            if self.state_machine.current != PetState.SLEEPING:
                self.state_machine.set(PetState.SLEEPING)
                self.set_expression("小乖")
                self.say("摆了，先眯一会儿")
            return
        if self.state_machine.current == PetState.SLEEPING:
            return
        roll = random.random()
        if self.auto_wander and roll < 0.38:
            self._wander()
        elif roll < 0.82:
            self.react()
        else:
            self.say(random.choice(self.phrases.passive))

    def _wander(self) -> None:
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        if not screen:
            return
        area = screen.availableGeometry()
        target_x = random.randint(area.left(), max(area.left(), area.right() - self.width()))
        target_y = random.randint(area.top() + 60, max(area.top() + 60, area.bottom() - self.height()))
        distance = (QPoint(target_x, target_y) - self.pos()).manhattanLength()
        duration = int(min(4500, max(900, distance * 5)) / self.settings.move_speed)

        if self._move_animation:
            self._move_animation.stop()
        animation = QPropertyAnimation(self, b"pos", self)
        animation.setStartValue(self.pos())
        animation.setEndValue(QPoint(target_x, target_y))
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        animation.finished.connect(self._finish_wander)
        self._move_animation = animation
        self.state_machine.set(PetState.WALKING)
        self.set_expression(random.choice(("兴奋", "阴险", "微微一笑")))
        animation.start()

    def _finish_wander(self) -> None:
        if self.state_machine.current == PetState.WALKING:
            self.state_machine.set(PetState.IDLE)
        self.set_expression(random.choice(("微微一笑", "呵呵", "开心")))

    def open_settings(self) -> None:
        self._touch()
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_settings(dialog.values())

    def open_user_data_directory(self) -> None:
        ensure_user_directories()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(user_data_root())))

    def apply_settings(self, settings: PetSettings) -> None:
        previous = self.settings
        if previous.start_with_windows != settings.start_with_windows:
            try:
                set_autostart(settings.start_with_windows)
            except OSError as error:
                QMessageBox.warning(self, "开机启动设置失败", str(error))
                settings = replace(settings, start_with_windows=previous.start_with_windows)

        position = self.pos()
        was_visible = self.isVisible()
        top_changed = previous.always_on_top != settings.always_on_top
        self.settings = settings
        self.config_manager.replace(settings)
        self.auto_wander = settings.auto_wander
        self.always_on_top = settings.always_on_top
        self._refresh_appearance()
        self._update_behavior_timer()
        self.set_expression(self.expression, animate=False)
        if (
            self.plugin_manager
            and previous.enabled_plugins != settings.enabled_plugins
        ):
            self.plugin_manager.reload()
        if top_changed:
            self._apply_window_flags()
            if was_visible:
                self.show()
                self.move(position)
        self.say("设置已保存")

    def set_auto_wander(self, enabled: bool) -> None:
        if self.auto_wander == enabled:
            return
        self.settings = replace(self.settings, auto_wander=enabled)
        self.config_manager.replace(self.settings)
        self.auto_wander = enabled
        self.say("自动溜达已开启" if enabled else "不走了，原地摆烂")

    def set_always_on_top(self, enabled: bool) -> None:
        if self.always_on_top == enabled:
            return
        self.apply_settings(replace(self.settings, always_on_top=enabled))
        self.say("黄豆继续盯着你" if enabled else "行，我低调一点")

    def save_position(self) -> None:
        self.settings = replace(
            self.settings,
            position_x=self.x(),
            position_y=self.y(),
        )
        self.config_manager.replace(self.settings)

    def shutdown(self) -> None:
        self._behavior_timer.stop()
        self._bubble_timer.stop()
        if self._move_animation:
            self._move_animation.stop()
        self.save_position()

    def build_context_menu(self) -> QMenu:
        menu = QMenu(self)
        random_action = QAction("随机表情", menu)
        random_action.triggered.connect(self.react)
        menu.addAction(random_action)

        speak_action = QAction("说句话", menu)
        speak_action.triggered.connect(lambda: self.say(random.choice(self.phrases.passive)))
        menu.addAction(speak_action)

        reload_phrases = QAction("重新加载文案", menu)
        reload_phrases.triggered.connect(self._reload_phrases)
        menu.addAction(reload_phrases)

        reset_phrases = QAction("恢复默认文案", menu)
        reset_phrases.triggered.connect(self._reset_phrases)
        menu.addAction(reset_phrases)

        open_data = QAction("打开数据目录", menu)
        open_data.triggered.connect(self.open_user_data_directory)
        menu.addAction(open_data)

        expression_menu = menu.addMenu("选择表情")
        for name in self.atlas.names:
            action = QAction(name, expression_menu)
            action.triggered.connect(lambda checked=False, value=name: self.react(value))
            expression_menu.addAction(action)

        if self.plugin_manager:
            plugin_menu = menu.addMenu("实用插件")
            self.plugin_manager.populate_menu(plugin_menu)

        menu.addSeparator()
        settings_action = QAction("设置...", menu)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        wander_action = QAction("自动走动", menu)
        wander_action.setCheckable(True)
        wander_action.setChecked(self.auto_wander)
        wander_action.toggled.connect(self.set_auto_wander)
        menu.addAction(wander_action)

        top_action = QAction("始终置顶", menu)
        top_action.setCheckable(True)
        top_action.setChecked(self.always_on_top)
        top_action.toggled.connect(self.set_always_on_top)
        menu.addAction(top_action)

        menu.addSeparator()
        hide_action = QAction("隐藏黄豆", menu)
        hide_action.triggered.connect(self.hide)
        menu.addAction(hide_action)
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        return menu

    def _reload_phrases(self) -> None:
        self.phrases.reload()
        self.say("文案已重新加载")

    def _reset_phrases(self) -> None:
        result = QMessageBox.question(
            self,
            "恢复默认文案",
            "这会覆盖当前 data\\phrases.json，确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        self.phrases.reset_to_defaults()
        self.say("默认文案已恢复")

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # noqa: N802
        self._touch()
        self.build_context_menu().exec(event.globalPos())

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._touch()
            if self._move_animation:
                self._move_animation.stop()
            self.state_machine.set(PetState.DRAGGING)
            self._dragging = True
            self._drag_moved = False
            self._drag_announced = False
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_position = event.globalPosition().toPoint() - self._drag_offset
            if (new_position - self.pos()).manhattanLength() > 3:
                self._drag_moved = True
            self.move(new_position)
            if self._drag_moved and not self._drag_announced:
                self._drag_announced = True
                self.set_expression("紧张")
                self.say(random.choice(self.phrases.drag))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.state_machine.set(PetState.IDLE)
            if self._drag_moved:
                self.save_position()
            else:
                self.react()
            event.accept()
            return
        super().mouseReleaseEvent(event)
