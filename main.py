"""黄豆桌宠启动入口。"""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from huangdou.assets import SpriteAtlas
from huangdou.config import ConfigManager
from huangdou.logging_setup import configure_logging, install_exception_hooks
from huangdou.pet import PetWindow
from huangdou.phrases import PhraseRepository
from huangdou.plugins.base import PluginContext
from huangdou.plugins.manager import PluginManager
from huangdou.state import StateMachine


LOGGER = logging.getLogger(__name__)


def create_tray(
    app: QApplication,
    pet: PetWindow,
    plugins: PluginManager,
) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(QIcon(pet.atlas.pixmap("微微一笑", 64)), app)
    tray.setToolTip("TiebaPet - 黄豆桌宠")
    menu = QMenu()

    def rebuild_menu() -> None:
        menu.clear()
        show_action = QAction("显示黄豆", menu)
        show_action.triggered.connect(
            lambda: (pet.show(), pet.raise_(), pet.activateWindow())
        )
        menu.addAction(show_action)

        random_action = QAction("随机表情", menu)
        random_action.triggered.connect(lambda: (pet.show(), pet.react()))
        menu.addAction(random_action)

        settings_action = QAction("设置...", menu)
        settings_action.triggered.connect(pet.open_settings)
        menu.addAction(settings_action)

        plugin_menu = menu.addMenu("实用插件")
        plugins.populate_menu(plugin_menu)

        menu.addSeparator()
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)

    menu.aboutToShow.connect(rebuild_menu)
    rebuild_menu()
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: (pet.show(), pet.raise_())
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )
    tray.show()
    return tray


def main() -> int:
    log_file = configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("TiebaPet")
    app.setQuitOnLastWindowClosed(False)
    install_exception_hooks()
    LOGGER.info("黄豆桌宠启动，日志文件：%s", log_file)

    try:
        atlas = SpriteAtlas()
        config_path = os.environ.get("TIEBAPET_CONFIG_PATH") or os.environ.get(
            "HUANGDOU_CONFIG_PATH"
        )
        phrases_path = os.environ.get("TIEBAPET_PHRASES_PATH") or os.environ.get(
            "HUANGDOU_PHRASES_PATH"
        )
        config = ConfigManager(Path(config_path)) if config_path else ConfigManager()
        phrases = (
            PhraseRepository(Path(phrases_path))
            if phrases_path
            else PhraseRepository()
        )
    except Exception as error:
        LOGGER.exception("启动失败")
        print(f"启动失败：{error}", file=sys.stderr)
        return 1

    state = StateMachine()
    pet = PetWindow(atlas, config, phrases, state)
    plugin_context = PluginContext(pet=pet, config=config, state=state)
    extension_path = os.environ.get("TIEBAPET_EXTENSIONS_PATH") or os.environ.get(
        "HUANGDOU_EXTENSIONS_PATH"
    )
    plugins = PluginManager(
        plugin_context,
        Path(extension_path) if extension_path else None,
    )
    plugins.load_all()
    pet.set_plugin_manager(plugins)
    tray = create_tray(app, pet, plugins)

    def shutdown() -> None:
        LOGGER.info("黄豆桌宠退出")
        plugins.shutdown()
        pet.shutdown()

    app.aboutToQuit.connect(shutdown)
    pet.show()
    pet.say("黄豆 2.1 已上线，今天也得整点活", 4200)

    # 自动化测试使用，正常启动时不会触发。
    if (
        os.environ.get("TIEBAPET_SMOKE_TEST") == "1"
        or os.environ.get("HUANGDOU_SMOKE_TEST") == "1"
    ):
        QTimer.singleShot(700, app.quit)

    # 防止 Qt 对象被垃圾回收。
    app._huangdou_tray = tray  # type: ignore[attr-defined]
    app._huangdou_pet = pet  # type: ignore[attr-defined]
    app._huangdou_plugins = plugins  # type: ignore[attr-defined]
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
