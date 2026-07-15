"""Windows 开机启动管理。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "TiebaPet"
LEGACY_VALUE_NAME = "HuangdouPet"


def _startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    project_root = Path(__file__).resolve().parent.parent
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    executable = pythonw if pythonw.exists() else Path(sys.executable)
    return f'"{executable}" "{project_root / "main.py"}"'


def set_autostart(enabled: bool) -> None:
    """为当前 Windows 用户开启或关闭黄豆的开机启动。"""
    if os.name != "nt":
        return
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        RUN_KEY,
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        if enabled:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, _startup_command())
        for value_name in (LEGACY_VALUE_NAME,) if enabled else (VALUE_NAME, LEGACY_VALUE_NAME):
            try:
                winreg.DeleteValue(key, value_name)
            except FileNotFoundError:
                pass
