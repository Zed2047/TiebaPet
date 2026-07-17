"""桌宠设置窗口。"""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from .config import PetSettings
from .paths import user_data_root


class SettingsDialog(QDialog):
    """集中调整外观、行为和番茄钟选项。"""

    def __init__(self, settings: PetSettings, parent=None) -> None:
        super().__init__(parent)
        self._original = settings
        self.setWindowTitle("黄豆设置")
        self.setMinimumWidth(390)

        layout = QVBoxLayout(self)
        appearance = QGroupBox("外观")
        appearance_form = QFormLayout(appearance)
        self.sprite_size = self._spin(70, 220, settings.sprite_size, " px")
        self.font_size = self._spin(12, 32, settings.font_size, " px")
        self.bubble_height = self._spin(65, 140, settings.bubble_height, " px")
        appearance_form.addRow("黄豆大小", self.sprite_size)
        appearance_form.addRow("回复字体", self.font_size)
        appearance_form.addRow("气泡高度", self.bubble_height)
        layout.addWidget(appearance)

        behavior = QGroupBox("行为")
        behavior_form = QFormLayout(behavior)
        self.auto_wander = QCheckBox("允许黄豆自动溜达")
        self.auto_wander.setChecked(settings.auto_wander)
        self.always_on_top = QCheckBox("始终显示在其他窗口上方")
        self.always_on_top.setChecked(settings.always_on_top)
        self.start_with_windows = QCheckBox("登录 Windows 后自动启动")
        self.start_with_windows.setChecked(settings.start_with_windows)
        self.behavior_interval = self._spin(
            3, 120, settings.behavior_interval_seconds, " 秒"
        )
        self.sleep_after = self._spin(1, 180, settings.sleep_after_minutes, " 分钟")
        self.move_speed = QDoubleSpinBox()
        self.move_speed.setRange(0.5, 3.0)
        self.move_speed.setSingleStep(0.1)
        self.move_speed.setValue(settings.move_speed)
        self.move_speed.setSuffix(" 倍")
        behavior_form.addRow(self.auto_wander)
        behavior_form.addRow(self.always_on_top)
        behavior_form.addRow(self.start_with_windows)
        behavior_form.addRow("随机行为间隔", self.behavior_interval)
        behavior_form.addRow("多久后睡觉", self.sleep_after)
        behavior_form.addRow("移动速度", self.move_speed)
        layout.addWidget(behavior)

        plugins = QGroupBox("内置插件")
        plugins_form = QFormLayout(plugins)
        enabled = settings.enabled_plugins
        self.reminder_plugin = QCheckBox("定时提醒")
        self.reminder_plugin.setChecked(enabled.get("reminder", True))
        self.pomodoro_plugin = QCheckBox("番茄钟")
        self.pomodoro_plugin.setChecked(enabled.get("pomodoro", True))
        self.system_info_plugin = QCheckBox("系统状态")
        self.system_info_plugin.setChecked(enabled.get("system_info", True))
        plugins_form.addRow(self.reminder_plugin)
        plugins_form.addRow(self.pomodoro_plugin)
        plugins_form.addRow(self.system_info_plugin)
        layout.addWidget(plugins)

        pomodoro = QGroupBox("番茄钟")
        pomodoro_form = QFormLayout(pomodoro)
        self.work_minutes = self._spin(1, 120, settings.pomodoro_work_minutes, " 分钟")
        self.break_minutes = self._spin(1, 60, settings.pomodoro_break_minutes, " 分钟")
        pomodoro_form.addRow("专注时长", self.work_minutes)
        pomodoro_form.addRow("休息时长", self.break_minutes)
        layout.addWidget(pomodoro)

        hint = QLabel(f"用户数据：{user_data_root()}")
        hint.setStyleSheet("color: #666;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _spin(minimum: int, maximum: int, value: int, suffix: str) -> QSpinBox:
        widget = QSpinBox()
        widget.setRange(minimum, maximum)
        widget.setValue(value)
        widget.setSuffix(suffix)
        return widget

    def values(self) -> PetSettings:
        enabled_plugins = dict(self._original.enabled_plugins)
        enabled_plugins.update(
            {
                "reminder": self.reminder_plugin.isChecked(),
                "pomodoro": self.pomodoro_plugin.isChecked(),
                "system_info": self.system_info_plugin.isChecked(),
            }
        )
        return replace(
            self._original,
            sprite_size=self.sprite_size.value(),
            font_size=self.font_size.value(),
            bubble_height=self.bubble_height.value(),
            auto_wander=self.auto_wander.isChecked(),
            always_on_top=self.always_on_top.isChecked(),
            behavior_interval_seconds=self.behavior_interval.value(),
            move_speed=self.move_speed.value(),
            sleep_after_minutes=self.sleep_after.value(),
            start_with_windows=self.start_with_windows.isChecked(),
            pomodoro_work_minutes=self.work_minutes.value(),
            pomodoro_break_minutes=self.break_minutes.value(),
            enabled_plugins=enabled_plugins,
        )
