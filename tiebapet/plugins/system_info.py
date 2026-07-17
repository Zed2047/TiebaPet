"""系统时间与资源状态插件。"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QMenu

from .base import BasePlugin

try:
    import psutil
except ImportError:  # pragma: no cover - 依赖缺失时仍可显示时间
    psutil = None


class SystemInfoPlugin(BasePlugin):
    plugin_id = "system_info"
    display_name = "系统状态"

    def status_text(self) -> str:
        now = datetime.now().strftime("%H:%M")
        if psutil is None:
            return f"现在 {now}，该干正事了老哥"
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory().percent
        return f"现在 {now}\nCPU {cpu:.0f}%　内存 {memory:.0f}%"

    def _show_status(self) -> None:
        if self.context:
            self.context.pet.set_expression("微微一笑")
            self.context.pet.say(self.status_text(), 5000)

    def populate_menu(self, menu: QMenu) -> None:
        action = menu.addAction("查看当前状态")
        action.triggered.connect(self._show_status)
