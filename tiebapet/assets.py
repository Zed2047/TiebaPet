"""加载独立黄豆表情，并在内存中去除白色背景。"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

from .paths import resource_root, user_data_root
from .phrases import EXPRESSION_NAMES


ASSET_DIR = resource_root() / "assets" / "expressions"
DEFAULT_CACHE_DIR = user_data_root() / "cache" / "expressions"
ALGORITHM_VERSION = "white-flood-v2"
LOGGER = logging.getLogger(__name__)


class SpriteAtlas:
    """加载独立图片，并在内存中完成去背景和统一缩放。"""

    def __init__(
        self,
        asset_dir: Path = ASSET_DIR,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        use_cache: bool = True,
    ) -> None:
        self.asset_dir = Path(asset_dir)
        self.cache_dir = Path(cache_dir)
        self.use_cache = use_cache
        self.cache_hits = 0
        self.processed_count = 0
        self._images: dict[str, QImage] = {}
        self._pixmaps: dict[str, tuple[int, QPixmap]] = {}
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    @property
    def names(self) -> tuple[str, ...]:
        return EXPRESSION_NAMES

    def _load(self) -> None:
        if not self.asset_dir.exists():
            raise FileNotFoundError(f"素材目录不存在：{self.asset_dir}")

        supported = {".png", ".jpg", ".jpeg"}
        source_files = {
            path.stem: path
            for path in self.asset_dir.iterdir()
            if path.is_file() and path.suffix.lower() in supported
        }
        missing = set(EXPRESSION_NAMES) - source_files.keys()
        if missing:
            raise RuntimeError(f"黄豆素材缺失：{', '.join(sorted(missing))}")

        for name in EXPRESSION_NAMES:
            path = source_files[name]
            cache_path = self._cache_path(name, path)
            cached = QImage(str(cache_path)) if self.use_cache and cache_path.exists() else QImage()
            if not cached.isNull():
                self._images[name] = cached.convertToFormat(QImage.Format.Format_ARGB32)
                self.cache_hits += 1
                continue
            source = self._read_image(path)
            transparent = self._remove_connected_background(source)
            image = self._to_qimage(transparent)
            self._images[name] = image
            self.processed_count += 1
            if self.use_cache:
                self._save_cache(name, cache_path, image)

        LOGGER.info(
            "表情加载完成：缓存命中 %s，重新处理 %s",
            self.cache_hits,
            self.processed_count,
        )

    @staticmethod
    def _cache_path_for(cache_dir: Path, name: str, source_path: Path) -> Path:
        digest = hashlib.sha256()
        digest.update(ALGORITHM_VERSION.encode("ascii"))
        digest.update(source_path.read_bytes())
        return cache_dir / f"{name}-{digest.hexdigest()[:16]}.png"

    def _cache_path(self, name: str, source_path: Path) -> Path:
        return self._cache_path_for(self.cache_dir, name, source_path)

    def _save_cache(self, name: str, path: Path, image: QImage) -> None:
        try:
            for stale in self.cache_dir.glob(f"{name}-*.png"):
                if stale != path:
                    stale.unlink(missing_ok=True)
            if not image.save(str(path), "PNG"):
                raise OSError("Qt 无法保存 PNG")
        except OSError:
            LOGGER.exception("表情缓存写入失败：%s", path)

    @staticmethod
    def _read_image(path: Path) -> Any:
        import cv2
        import numpy as np

        # imdecode + fromfile 可以稳定读取包含中文的 Windows 路径。
        encoded = np.fromfile(path, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise FileNotFoundError(f"无法读取素材：{path}")
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGBA)
        if image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)

    @staticmethod
    def _remove_connected_background(source: Any) -> Any:
        """只移除与画布边缘连通的白底，保留眼睛和牙齿中的白色。"""
        import cv2
        import numpy as np

        height, width = source.shape[:2]
        bgr = cv2.cvtColor(source, cv2.COLOR_RGBA2BGR)

        # 加一圈白边后从左上角填充，可覆盖所有与画布外部连通的白色区域。
        padded = cv2.copyMakeBorder(
            bgr, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )
        mask = np.zeros((padded.shape[0] + 2, padded.shape[1] + 2), dtype=np.uint8)
        flags = (
            4
            | cv2.FLOODFILL_MASK_ONLY
            | cv2.FLOODFILL_FIXED_RANGE
            | (255 << 8)
        )
        cv2.floodFill(
            padded,
            mask,
            (0, 0),
            (0, 0, 0),
            (46, 46, 46),
            (46, 46, 46),
            flags,
        )

        result = source.copy()
        outside = mask[2:-2, 2:-2] == 255
        result[outside, 3] = 0

        visible = (result[:, :, 3] > 0).astype(np.uint8)
        points = cv2.findNonZero(visible)
        if points is None:
            raise RuntimeError("素材去背景后为空，请检查原始图片。")
        x, y, box_width, box_height = cv2.boundingRect(points)
        padding = max(3, round(max(width, height) * 0.012))
        left = max(0, x - padding)
        top = max(0, y - padding)
        right = min(width, x + box_width + padding)
        bottom = min(height, y + box_height + padding)
        return np.ascontiguousarray(result[top:bottom, left:right])

    @staticmethod
    def _to_qimage(rgba: Any) -> QImage:
        height, width = rgba.shape[:2]
        image = QImage(
            rgba.data,
            width,
            height,
            rgba.strides[0],
            QImage.Format.Format_RGBA8888,
        )
        # 深拷贝后，QImage 不再依赖 NumPy 数组的生命周期。
        return image.copy()

    def image(self, name: str) -> QImage:
        return self._images[name]

    def pixmap(self, name: str, size: int = 128) -> QPixmap:
        cached = self._pixmaps.get(name)
        if not cached or cached[0] != size:
            pixmap = QPixmap.fromImage(self._images[name]).scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._pixmaps[name] = (size, pixmap)
        return self._pixmaps[name][1]
