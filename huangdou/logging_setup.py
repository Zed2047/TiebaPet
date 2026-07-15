"""运行日志和未捕获异常记录。"""

from __future__ import annotations

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from .paths import ensure_user_directories, user_data_root


def configure_logging(log_file: Path | None = None) -> Path:
    ensure_user_directories()
    target = log_file or (user_data_root() / "logs" / "tieba-pet.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not any(isinstance(handler, RotatingFileHandler) for handler in root.handlers):
        handler = RotatingFileHandler(
            target,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root.addHandler(handler)
    logging.getLogger(__name__).info("日志初始化：%s", target)
    return target


def install_exception_hooks() -> None:
    logger = logging.getLogger("huangdou.crash")

    def handle_exception(exc_type, exc_value, traceback) -> None:
        logger.critical(
            "未捕获异常",
            exc_info=(exc_type, exc_value, traceback),
        )
        app = QApplication.instance()
        if app:
            QMessageBox.critical(
                None,
                "黄豆遇到错误",
                f"{exc_value}\n\n错误详情已写入 logs\\tieba-pet.log",
            )

    sys.excepthook = handle_exception

    def handle_thread_exception(args: threading.ExceptHookArgs) -> None:
        handle_exception(args.exc_type, args.exc_value, args.exc_traceback)

    threading.excepthook = handle_thread_exception
