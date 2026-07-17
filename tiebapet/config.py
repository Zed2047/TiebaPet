"""黄豆桌宠的配置读取与持久化。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace as dataclass_replace
from pathlib import Path
from typing import Any

from .paths import ensure_user_directories, migrate_resource_file, user_data_root


DEFAULT_CONFIG_PATH = user_data_root() / "config.json"


@dataclass(slots=True)
class PetSettings:
    """用户可以在设置窗口中修改的选项。"""

    sprite_size: int = 110
    font_size: int = 17
    bubble_height: int = 82
    auto_wander: bool = True
    always_on_top: bool = True
    behavior_interval_seconds: int = 6
    move_speed: float = 1.0
    sleep_after_minutes: int = 10
    start_with_windows: bool = False
    pomodoro_work_minutes: int = 25
    pomodoro_break_minutes: int = 5
    position_x: int | None = None
    position_y: int | None = None
    enabled_plugins: dict[str, bool] = field(
        default_factory=lambda: {
            "reminder": True,
            "pomodoro": True,
            "system_info": True,
        }
    )
    plugin_state: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PetSettings":
        defaults = cls()
        values = asdict(defaults)
        for key in values:
            if key in raw:
                values[key] = raw[key]
        if not isinstance(values["enabled_plugins"], dict):
            values["enabled_plugins"] = asdict(defaults)["enabled_plugins"]
        if not isinstance(values["plugin_state"], dict):
            values["plugin_state"] = {}
        else:
            values["plugin_state"] = {
                str(plugin_id): state
                for plugin_id, state in values["plugin_state"].items()
                if isinstance(state, dict)
            }
        return cls(**values)


class ConfigManager:
    """负责加载、保存和更新桌宠配置。"""

    def __init__(self, path: Path = DEFAULT_CONFIG_PATH) -> None:
        self.path = Path(path)
        if self.path == DEFAULT_CONFIG_PATH:
            ensure_user_directories()
            migrate_resource_file("data/config.json", self.path)
        self.settings = self.load()

    def load(self) -> PetSettings:
        if not self.path.exists():
            settings = PetSettings()
            self.settings = settings
            self.save()
            return settings
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("配置根节点必须是对象")
            return PetSettings.from_dict(raw)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            # 配置损坏时恢复默认值，保证桌宠仍能启动。
            settings = PetSettings()
            self.settings = settings
            self.save()
            return settings

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(asdict(self.settings), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def replace(self, settings: PetSettings) -> None:
        # 窗口设置可能持有旧快照，始终保留插件刚写入的运行状态。
        self.settings = dataclass_replace(
            settings,
            plugin_state=self.settings.plugin_state,
        )
        self.save()

    def plugin_state(self, plugin_id: str) -> dict[str, Any]:
        return dict(self.settings.plugin_state.get(plugin_id, {}))

    def set_plugin_state(self, plugin_id: str, state: dict[str, Any]) -> None:
        states = dict(self.settings.plugin_state)
        states[plugin_id] = state
        self.settings = PetSettings.from_dict(
            {**asdict(self.settings), "plugin_state": states}
        )
        self.save()
