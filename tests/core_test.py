"""黄豆 2.1 配置、状态和插件测试。"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
TEST_DATA = TemporaryDirectory()
os.environ["HUANGDOU_DATA_DIR"] = TEST_DATA.name
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from huangdou.assets import SpriteAtlas  # noqa: E402
from huangdou.config import ConfigManager  # noqa: E402
from huangdou.pet import PetWindow  # noqa: E402
from huangdou.phrases import PhraseRepository  # noqa: E402
from huangdou.plugins.base import PluginContext  # noqa: E402
from huangdou.plugins.manager import PluginManager  # noqa: E402
from huangdou.plugins.pomodoro import PomodoroPlugin  # noqa: E402
from huangdou.plugins.reminder import ReminderPlugin  # noqa: E402
from huangdou.plugins.system_info import SystemInfoPlugin  # noqa: E402
from huangdou.state import PetState, StateMachine  # noqa: E402


def main() -> int:
    app = QApplication.instance() or QApplication([])
    atlas = SpriteAtlas()
    assert atlas.processed_count == 31
    cached_atlas = SpriteAtlas()
    assert cached_atlas.cache_hits == 31
    assert cached_atlas.processed_count == 0

    with TemporaryDirectory() as directory:
        root = Path(directory)
        config = ConfigManager(root / "config.json")
        changed = replace(config.settings, font_size=20, sprite_size=120)
        config.replace(changed)
        reloaded = ConfigManager(root / "config.json")
        assert reloaded.settings.font_size == 20
        assert reloaded.settings.sprite_size == 120

        phrases = PhraseRepository(root / "phrases.json")
        raw = json.loads((root / "phrases.json").read_text(encoding="utf-8"))
        raw["phrases"]["开心"] = ["测试文案"]
        (root / "phrases.json").write_text(
            json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        phrases.reload()
        assert phrases.for_expression("开心") == "测试文案"

        state = StateMachine()
        pet = PetWindow(atlas, reloaded, phrases, state)
        pet.show()
        app.processEvents()
        assert "font-size: 20px" in pet.bubble.styleSheet()
        assert pet.settings.sprite_size == 120

        extension_dir = root / "extensions"
        extension_dir.mkdir()
        (extension_dir / "demo.py").write_text(
            "from huangdou.plugins.base import BasePlugin\n"
            "class DemoPlugin(BasePlugin):\n"
            "    plugin_id = 'demo'\n"
            "    display_name = '测试插件'\n"
            "    def populate_menu(self, menu):\n"
            "        menu.addAction('测试')\n",
            encoding="utf-8",
        )
        (extension_dir / "incompatible.py").write_text(
            "from huangdou.plugins.base import BasePlugin\n"
            "class OldPlugin(BasePlugin):\n"
            "    api_version = 99\n"
            "    plugin_id = 'old'\n"
            "    display_name = '旧插件'\n"
            "    def populate_menu(self, menu): pass\n",
            encoding="utf-8",
        )
        context = PluginContext(pet=pet, config=reloaded, state=state)
        manager = PluginManager(context, extension_dir)
        manager.load_all()
        pet.set_plugin_manager(manager)
        assert set(manager.plugins) == {"reminder", "pomodoro", "system_info", "demo"}
        assert len(manager.errors) == 1

        reminder = manager.get("reminder")
        assert isinstance(reminder, ReminderPlugin)
        reminder.schedule(1, "测试提醒一")
        reminder.schedule(2, "测试提醒二")
        assert reminder.poll_timer and reminder.poll_timer.isActive()
        assert len(reloaded.plugin_state("reminder")["items"]) == 2

        pomodoro = manager.get("pomodoro")
        assert isinstance(pomodoro, PomodoroPlugin)
        pomodoro.start_work()
        assert state.current == PetState.WORKING
        assert reloaded.plugin_state("pomodoro")["active"] is True
        pomodoro.stop_timer(announce=False)
        assert state.current == PetState.IDLE
        assert reloaded.plugin_state("pomodoro")["active"] is False

        system_info = manager.get("system_info")
        assert isinstance(system_info, SystemInfoPlugin)
        assert "CPU" in system_info.status_text()

        menu = pet.build_context_menu()
        assert menu.actions()
        assert any(action.text() == "打开用户数据目录" for action in menu.actions())
        manager.shutdown()
        pet.shutdown()
        pet.close()

    TEST_DATA.cleanup()
    print("核心测试通过：配置、JSON 文案、状态机、内置插件和外部插件均正常")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
