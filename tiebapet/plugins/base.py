"""插件接口与运行上下文。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMenu

from ..config import ConfigManager
from ..state import PetState, StateMachine


@dataclass(slots=True)
class PluginContext:
    pet: Any
    config: ConfigManager
    state: StateMachine

    def notify(
        self,
        text: str,
        expression: str = "疑问",
        duration_ms: int = 5000,
    ) -> None:
        self.state.set(PetState.REMINDING)
        self.pet.set_expression(expression)
        self.pet.say(text, duration_ms)

        def restore_idle() -> None:
            if self.state.current == PetState.REMINDING:
                self.state.set(PetState.IDLE)

        QTimer.singleShot(duration_ms, restore_idle)


class BasePlugin:
    api_version = 1
    plugin_id = "base"
    display_name = "基础插件"

    def __init__(self) -> None:
        self.context: PluginContext | None = None

    def start(self, context: PluginContext) -> None:
        self.context = context

    def stop(self) -> None:
        self.context = None

    def populate_menu(self, menu: QMenu) -> None:
        raise NotImplementedError
