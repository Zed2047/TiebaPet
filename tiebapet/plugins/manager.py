"""插件注册、加载与菜单装配。"""

from __future__ import annotations

import importlib.util
import inspect
import logging
from pathlib import Path

from PySide6.QtWidgets import QMenu

from .base import BasePlugin, PluginContext
from .pomodoro import PomodoroPlugin
from .reminder import ReminderPlugin
from .system_info import SystemInfoPlugin
from ..paths import extensions_root


LOGGER = logging.getLogger(__name__)


class PluginManager:
    def __init__(
        self,
        context: PluginContext,
        extension_dir: Path | None = None,
    ) -> None:
        self.context = context
        self.plugins: dict[str, BasePlugin] = {}
        self.errors: list[str] = []
        self.extension_dir = extension_dir or (
            extensions_root()
        )

    def _register(self, plugin: BasePlugin) -> None:
        enabled = self.context.config.settings.enabled_plugins
        if not enabled.get(plugin.plugin_id, True) or plugin.plugin_id in self.plugins:
            return
        if plugin.api_version != 1:
            raise RuntimeError(
                f"{plugin.plugin_id} 使用插件 API {plugin.api_version}，当前只支持 API 1"
            )
        plugin.start(self.context)
        self.plugins[plugin.plugin_id] = plugin

    def load_all(self) -> None:
        for plugin in (ReminderPlugin(), PomodoroPlugin(), SystemInfoPlugin()):
            self._register(plugin)
        self._load_extensions()

    def _load_extensions(self) -> None:
        self.extension_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.extension_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    f"tiebapet_extension_{path.stem}", path
                )
                if not spec or not spec.loader:
                    raise ImportError("无法创建模块加载器")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                classes = [
                    item
                    for item in vars(module).values()
                    if inspect.isclass(item)
                    and issubclass(item, BasePlugin)
                    and item is not BasePlugin
                    and item.__module__ == module.__name__
                ]
                for plugin_class in classes:
                    self._register(plugin_class())
            except Exception as error:  # 插件错误不能阻止桌宠启动
                self.errors.append(f"{path.name}: {error}")
                LOGGER.exception("插件加载失败：%s", path)

    def reload(self) -> None:
        self.shutdown()
        self.errors.clear()
        self.load_all()

    def populate_menu(self, menu: QMenu) -> None:
        if not self.plugins:
            action = menu.addAction("暂无已启用插件")
            action.setEnabled(False)
            return
        summary = menu.addAction(f"已加载 {len(self.plugins)} 个插件")
        summary.setEnabled(False)
        location = menu.addAction(f"目录：{self.extension_dir}")
        location.setEnabled(False)
        menu.addSeparator()
        for plugin in self.plugins.values():
            submenu = menu.addMenu(plugin.display_name)
            try:
                plugin.populate_menu(submenu)
            except Exception as error:
                self.errors.append(f"{plugin.plugin_id}: {error}")
                LOGGER.exception("插件菜单创建失败：%s", plugin.plugin_id)
                failed = submenu.addAction("插件运行失败，请查看日志")
                failed.setEnabled(False)
        if self.errors:
            menu.addSeparator()
            error_action = menu.addAction(f"{len(self.errors)} 个插件加载失败")
            error_action.setEnabled(False)

    def get(self, plugin_id: str) -> BasePlugin | None:
        return self.plugins.get(plugin_id)

    def shutdown(self) -> None:
        for plugin in self.plugins.values():
            try:
                plugin.stop()
            except Exception:
                LOGGER.exception("插件关闭失败：%s", plugin.plugin_id)
        self.plugins.clear()
