"""开发环境和打包环境共用的资源、用户数据路径。"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


APP_DIR_NAME = "TiebaPet"
LEGACY_APP_DIR_NAME = "HuangdouPet"


def resource_root() -> Path:
    """返回只读程序资源目录，兼容 PyInstaller。"""
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return Path(bundled)
    return Path(__file__).resolve().parent.parent


def user_data_root() -> Path:
    """返回可写用户目录，可用环境变量覆盖以便自动测试。"""
    override = os.environ.get("TIEBAPET_DATA_DIR") or os.environ.get(
        "HUANGDOU_DATA_DIR"
    )
    if override:
        return Path(override)
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_DIR_NAME
    return Path.home() / ".tieba-pet"


def migrate_legacy_user_directory() -> bool:
    """首次使用 TiebaPet 时复制旧 HuangdouPet 数据，不删除或覆盖旧目录。"""
    if os.environ.get("TIEBAPET_DATA_DIR") or os.environ.get("HUANGDOU_DATA_DIR"):
        return False
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return False
    legacy = Path(appdata) / LEGACY_APP_DIR_NAME
    destination = Path(appdata) / APP_DIR_NAME
    if destination.exists() or not legacy.exists():
        return False
    shutil.copytree(legacy, destination)
    return True


def ensure_user_directories() -> Path:
    migrate_legacy_user_directory()
    root = user_data_root()
    for path in (root, root / "logs", root / "cache" / "expressions", root / "extensions"):
        path.mkdir(parents=True, exist_ok=True)
    return root


def migrate_resource_file(relative_path: str, destination: Path) -> bool:
    """用户文件不存在时，从项目/安装包模板复制，绝不覆盖用户数据。"""
    if destination.exists():
        return False
    source = resource_root() / relative_path
    if not source.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True
