import hashlib
from pathlib import Path
from typing import Optional
from collections import OrderedDict
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSize


class ImageCache:


    def __init__(self, 
                 max_memory_mb: int = 200,
                 max_disk_mb: int = 1000,
                 cache_dir: Optional[Path] = None):

        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_disk_bytes = max_disk_mb * 1024 * 1024


        self._memory_cache: OrderedDict[str, tuple[QPixmap, int]] = OrderedDict()
        self._memory_size = 0


        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "mangareader" / "images"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)


        self._disk_size = self._calculate_disk_usage()

    def _calculate_disk_usage(self) -> int:

        total = 0
        for file in self.cache_dir.glob("*.cache"):
            total += file.stat().st_size
        return total

    def _make_cache_key(self, identifier: str, size: Optional[QSize] = None) -> str:

        if size:
            key = f"{identifier}_{size.width()}x{size.height()}"
        else:
            key = identifier
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:

        return self.cache_dir / f"{cache_key}.cache"

    def _evict_memory_lru(self, required_bytes: int):

        while self._memory_size + required_bytes > self.max_memory_bytes and self._memory_cache:

            key, (pixmap, size) = self._memory_cache.popitem(last=False)
            self._memory_size -= size

    def _evict_disk_lru(self, required_bytes: int):

        if self._disk_size + required_bytes <= self.max_disk_bytes:
            return


        cache_files = sorted(
            self.cache_dir.glob("*.cache"),
            key=lambda p: p.stat().st_atime
        )

        for file in cache_files:
            if self._disk_size + required_bytes <= self.max_disk_bytes:
                break

            size = file.stat().st_size
            file.unlink()
            self._disk_size -= size

    def _estimate_pixmap_size(self, pixmap: QPixmap) -> int:


        return pixmap.width() * pixmap.height() * 4

    def get(self, identifier: str, size: Optional[QSize] = None) -> Optional[QPixmap]:

        cache_key = self._make_cache_key(identifier, size)


        if cache_key in self._memory_cache:

            pixmap, pixmap_size = self._memory_cache.pop(cache_key)
            self._memory_cache[cache_key] = (pixmap, pixmap_size)
            return pixmap


        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            pixmap = QPixmap()
            if pixmap.load(str(cache_path)):

                pixmap_size = self._estimate_pixmap_size(pixmap)
                self._evict_memory_lru(pixmap_size)
                self._memory_cache[cache_key] = (pixmap, pixmap_size)
                self._memory_size += pixmap_size


                cache_path.touch()
                return pixmap

        return None

    def put(self, identifier: str, pixmap: QPixmap, size: Optional[QSize] = None, save_to_disk: bool = True):

        cache_key = self._make_cache_key(identifier, size)
        pixmap_size = self._estimate_pixmap_size(pixmap)


        self._evict_memory_lru(pixmap_size)
        self._memory_cache[cache_key] = (pixmap, pixmap_size)
        self._memory_size += pixmap_size


        if save_to_disk:
            cache_path = self._get_cache_path(cache_key)
            file_size = cache_path.stat().st_size if cache_path.exists() else 0


            estimated_disk_size = pixmap_size // 2  
            self._evict_disk_lru(estimated_disk_size)

            if pixmap.save(str(cache_path), "PNG"):

                new_file_size = cache_path.stat().st_size
                self._disk_size += new_file_size - file_size

    def has(self, identifier: str, size: Optional[QSize] = None) -> bool:

        cache_key = self._make_cache_key(identifier, size)
        return (cache_key in self._memory_cache or 
                self._get_cache_path(cache_key).exists())

    def clear_memory(self):

        self._memory_cache.clear()
        self._memory_size = 0

    def clear_disk(self):

        for file in self.cache_dir.glob("*.cache"):
            file.unlink()
        self._disk_size = 0

    def clear_all(self):

        self.clear_memory()
        self.clear_disk()

    def get_stats(self) -> dict:

        return {
            "memory_items": len(self._memory_cache),
            "memory_size_mb": self._memory_size / (1024 * 1024),
            "memory_max_mb": self.max_memory_bytes / (1024 * 1024),
            "disk_size_mb": self._disk_size / (1024 * 1024),
            "disk_max_mb": self.max_disk_bytes / (1024 * 1024),
        }



_global_cache: Optional[ImageCache] = None


def get_image_cache() -> ImageCache:

    global _global_cache
    if _global_cache is None:
        _global_cache = ImageCache()
    return _global_cache
