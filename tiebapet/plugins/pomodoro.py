"""支持重启恢复的番茄钟插件。"""

from __future__ import annotations

from time import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMenu

from ..state import PetState
from .base import BasePlugin, PluginContext


class PomodoroPlugin(BasePlugin):
    plugin_id = "pomodoro"
    display_name = "番茄钟"

    def __init__(self) -> None:
        super().__init__()
        self.timer: QTimer | None = None
        self.end_at = 0.0
        self.mode = "work"
        self.active = False

    @property
    def remaining_seconds(self) -> int:
        return max(0, int(self.end_at - time() + 0.999)) if self.active else 0

    def start(self, context: PluginContext) -> None:
        super().start(context)
        self.timer = QTimer(context.pet)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        stored = context.config.plugin_state(self.plugin_id)
        self.mode = stored.get("mode", "work")
        self.end_at = float(stored.get("end_at", 0))
        self.active = bool(stored.get("active", False))
        if self.active and self.remaining_seconds > 0:
            context.state.set(PetState.WORKING if self.mode == "work" else PetState.IDLE)
            self.timer.start()
        elif self.active:
            QTimer.singleShot(0, self._complete)

    def _save(self) -> None:
        if self.context:
            self.context.config.set_plugin_state(
                self.plugin_id,
                {"active": self.active, "mode": self.mode, "end_at": self.end_at},
            )

    def _start(self, mode: str, minutes: int) -> None:
        if not self.context:
            return
        self.mode = mode
        self.end_at = time() + max(1, minutes) * 60
        self.active = True
        self._save()
        if mode == "work":
            self.context.state.set(PetState.WORKING)
            self.context.pet.set_expression("真棒")
            self.context.pet.say("番茄钟启动，别摸了，开整！")
        else:
            self.context.state.set(PetState.IDLE)
            self.context.pet.set_expression("开心")
            self.context.pet.say("休息时间，起来润两步")
        if self.timer:
            self.timer.start()

    def start_work(self) -> None:
        if self.context:
            self._start("work", self.context.config.settings.pomodoro_work_minutes)

    def start_break(self) -> None:
        if self.context:
            self._start("break", self.context.config.settings.pomodoro_break_minutes)

    def stop_timer(self, announce: bool = True) -> None:
        if self.timer:
            self.timer.stop()
        self.active = False
        self.end_at = 0
        self._save()
        if self.context:
            self.context.state.set(PetState.IDLE)
            if announce:
                self.context.pet.say("番茄钟已停止")

    def _tick(self) -> None:
        if self.active and self.remaining_seconds <= 0:
            self._complete()

    def _complete(self) -> None:
        if self.timer:
            self.timer.stop()
        was_work = self.mode == "work"
        self.active = False
        self.end_at = 0
        self._save()
        if not self.context:
            return
        if was_work:
            self.context.notify("专注结束，赢！该休息一下了", "欢呼", 6500)
        else:
            self.context.notify("休息结束，下一轮开整？", "疑问", 6500)

    def _status_text(self) -> str:
        if not self.active:
            return "当前未运行"
        minutes, seconds = divmod(self.remaining_seconds, 60)
        label = "专注" if self.mode == "work" else "休息"
        return f"{label}剩余 {minutes:02d}:{seconds:02d}"

    def populate_menu(self, menu: QMenu) -> None:
        status = menu.addAction(self._status_text())
        status.setEnabled(False)
        menu.addSeparator()
        work = menu.addAction("开始专注")
        work.triggered.connect(self.start_work)
        rest = menu.addAction("开始休息")
        rest.triggered.connect(self.start_break)
        stop = menu.addAction("停止番茄钟")
        stop.setEnabled(self.active)
        stop.triggered.connect(self.stop_timer)

    def stop(self) -> None:
        # 关闭程序只停止本次 QTimer，保留 end_at 供下次启动恢复。
        if self.timer:
            self.timer.stop()
        BasePlugin.stop(self)
