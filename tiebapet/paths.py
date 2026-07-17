"""程序目录下的资源、数据、缓存、日志和插件路径。"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def application_root() -> Path:
    """返回程序目录；开发环境为项目根目录，打包后为 EXE 所在目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_root() -> Path:
    """返回只读资源目录，兼容 PyInstaller。"""
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return Path(bundled)
    return application_root()


def user_data_root() -> Path:
    """返回程序目录下的可编辑 data 目录，可用环境变量覆盖以便测试。"""
    override = os.environ.get("TIEBAPET_DATA_DIR")
    if override:
        return Path(override)
    return application_root() / "data"


def logs_root() -> Path:
    """返回程序目录下的日志目录。"""
    if os.environ.get("TIEBAPET_DATA_DIR"):
        return user_data_root() / "logs"
    return application_root() / "logs"


def extensions_root() -> Path:
    """返回程序目录下的第三方插件目录。"""
    if os.environ.get("TIEBAPET_DATA_DIR"):
        return user_data_root() / "extensions"
    return application_root() / "extensions"


def ensure_user_directories() -> Path:
    """创建程序运行所需的可写目录。"""
    root = user_data_root()
    for path in (
        root,
        root / "cache" / "expressions",
        logs_root(),
        extensions_root(),
    ):
        path.mkdir(parents=True, exist_ok=True)
    return root


def migrate_resource_file(relative_path: str, destination: Path) -> bool:
    """缺少可编辑文件时，从打包资源复制一份，不覆盖用户修改。"""
    if destination.exists():
        return False
    source = resource_root() / relative_path
    if not source.exists():
        return False
    try:
        if source.resolve() == destination.resolve():
            return False
    except OSError:
        pass
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True