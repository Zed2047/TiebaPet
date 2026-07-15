"""不打开真实桌面的基础冒烟测试。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
TEST_DATA = TemporaryDirectory()
os.environ["HUANGDOU_DATA_DIR"] = TEST_DATA.name
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from huangdou.assets import ASSET_DIR, SpriteAtlas  # noqa: E402
from huangdou.pet import PetWindow  # noqa: E402
from huangdou.phrases import EXPRESSION_NAMES, PASSIVE_PHRASES, PHRASES  # noqa: E402


def main() -> int:
    app = QApplication.instance() or QApplication([])
    atlas = SpriteAtlas()
    assert atlas.names == EXPRESSION_NAMES
    assert len(atlas.names) == 31
    assert set(PHRASES) == set(EXPRESSION_NAMES)
    source_files = [
        path for path in ASSET_DIR.iterdir()
        if path.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]
    assert len(source_files) == len(EXPRESSION_NAMES)

    for name in atlas.names:
        image = atlas.image(name)
        assert not image.isNull(), f"{name} 图片为空"
        assert image.hasAlphaChannel(), f"{name} 没有透明通道"
        pixmap = atlas.pixmap(name)
        assert not pixmap.isNull(), f"{name} 无法转为 Pixmap"
        assert max(pixmap.width(), pixmap.height()) == 128, f"{name} 显示尺寸未统一"

    all_phrases = "".join(text for values in PHRASES.values() for text in values)
    all_phrases += "".join(PASSIVE_PHRASES)
    for keyword in "典孝急绷乐赢润麻寄摆":
        assert keyword in all_phrases, f"台词缺少口头禅：{keyword}"

    pet = PetWindow(atlas)
    pet.show()
    app.processEvents()
    assert pet.expression == "微微一笑"
    pet.react("欢呼")
    app.processEvents()
    assert pet.expression == "欢呼"
    assert pet.bubble.isVisible()
    pet.close()
    TEST_DATA.cleanup()
    print(f"冒烟测试通过：{len(atlas.names)} 个表情、台词、窗口与交互组件均可加载。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
