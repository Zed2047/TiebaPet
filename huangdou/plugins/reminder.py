"""支持多条任务和重启恢复的定时提醒插件。"""

from __future__ import annotations

from datetime import datetime
from time import time
from uuid import uuid4

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QInputDialog, QMenu

from .base import BasePlugin, PluginContext


class ReminderPlugin(BasePlugin):
    plugin_id = "reminder"
    display_name = "定时提醒"

    def __init__(self) -> None:
        super().__init__()
        self.poll_timer: QTimer | None = None
        self.reminders: list[dict] = []

    def start(self, context: PluginContext) -> None:
        super().start(context)
        stored = context.config.plugin_state(self.plugin_id).get("items", [])
        self.reminders = [item for item in stored if self._valid_item(item)]
        self.poll_timer = QTimer(context.pet)
        self.poll_timer.setInterval(1000)
        self.poll_timer.timeout.connect(self._check_due)
        self.poll_timer.start()
        QTimer.singleShot(0, self._check_due)

    @staticmethod
    def _valid_item(item: object) -> bool:
        return (
            isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and isinstance(item.get("due_at"), (int, float))
            and isinstance(item.get("message"), str)
        )

    def _save(self) -> None:
        if self.context:
            self.context.config.set_plugin_state(self.plugin_id, {"items": self.reminders})

    def schedule(self, minutes: int, message: str) -> str:
        return self.schedule_seconds(max(1, minutes) * 60, message)

    def schedule_seconds(self, seconds: int, message: str) -> str:
        reminder_id = uuid4().hex
        self.reminders.append(
            {
                "id": reminder_id,
                "due_at": time() + max(1, seconds),
                "message": message.strip() or "老哥，到点了！",
            }
        )
        self._save()
        if self.context:
            self.context.pet.set_expression("真棒")
            self.context.pet.say("记住了，到点叫你")
        return reminder_id

    def cancel(self, reminder_id: str) -> None:
        self.reminders = [item for item in self.reminders if item["id"] != reminder_id]
        self._save()

    def clear(self) -> None:
        self.reminders.clear()
        self._save()
        if self.context:
            self.context.pet.say("提醒已全部清空")

    def _check_due(self) -> None:
        now = time()
        due = [item for item in self.reminders if item["due_at"] <= now]
        if not due:
            return
        due_ids = {item["id"] for item in due}
        self.reminders = [item for item in self.reminders if item["id"] not in due_ids]
        self._save()
        if self.context:
            messages = "\n".join(item["message"] for item in due[:3])
            if len(due) > 3:
                messages += f"\n还有 {len(due) - 3} 条提醒"
            self.context.notify(messages, "疑问", 7000)

    def _open_dialog(self) -> None:
        if not self.context:
            return
        minutes, accepted = QInputDialog.getInt(
            self.context.pet, "设置提醒", "多少分钟后提醒？", 5, 1, 1440
        )
        if not accepted:
            return
        message, accepted = QInputDialog.getText(
            self.context.pet,
            "提醒内容",
            "到点后让黄豆说什么？",
            text="老哥，到点了！",
        )
        if accepted:
            self.schedule(minutes, message)

    def populate_menu(self, menu: QMenu) -> None:
        action = menu.addAction("设置新提醒...")
        action.triggered.connect(self._open_dialog)
        if not self.reminders:
            empty = menu.addAction("当前没有提醒")
            empty.setEnabled(False)
            return
        menu.addSeparator()
        for item in sorted(self.reminders, key=lambda value: value["due_at"])[:8]:
            due_text = datetime.fromtimestamp(item["due_at"]).strftime("%m-%d %H:%M")
            label = item["message"].replace("\n", " ")[:16]
            submenu = menu.addMenu(f"{due_text}  {label}")
            cancel = submenu.addAction("取消这条提醒")
            cancel.triggered.connect(
                lambda checked=False, reminder_id=item["id"]: self.cancel(reminder_id)
            )
        clear = menu.addAction("清空全部提醒")
        clear.triggered.connect(self.clear)

    def stop(self) -> None:
        if self.poll_timer:
            self.poll_timer.stop()
        super().stop()
