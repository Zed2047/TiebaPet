"""桌宠行为状态机。"""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QObject, Signal


class PetState(str, Enum):
    IDLE = "idle"
    WALKING = "walking"
    SLEEPING = "sleeping"
    WORKING = "working"
    DRAGGING = "dragging"
    REMINDING = "reminding"


class StateMachine(QObject):
    """记录当前状态，并通知窗口和插件状态变化。"""

    changed = Signal(object, object)

    def __init__(self) -> None:
        super().__init__()
        self.current = PetState.IDLE

    def set(self, state: PetState) -> None:
        if state == self.current:
            return
        previous = self.current
        self.current = state
        self.changed.emit(previous, state)

