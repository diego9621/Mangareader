import asyncio
from pathlib import Path
from typing import Optional
from PIL import Image
from io import BytesIO
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QByteArray

from app.models import Chapter, Page
from app.sources.base import MangaSource
from app.sources.mangadex import MangaDexSource
from app.cache import get_image_cache


class PageLoader:
    def __init__(self):
        self.image_cache = get_image_cache()
        self._sources: dict[str, MangaSource] = {
            "mangadex": MangaDexSource()
        }
        self._prefetch_tasks: dict[str, asyncio.Task] = {}

    def get_source(self, source_name: str) -> Optional[MangaSource]:

        return self._sources.get(source_name)

    async def load_page_bytes(self, chapter: Chapter, page: Page) -> bytes:
        if page.local_path and Path(page.local_path).exists():
            return Path(page.local_path).read_bytes()

        if page.remote_url:
            source = self.get_source(chapter.source)
            if source:
                return await source.download_image(page.remote_url)

        raise ValueError(f"No valid source for page {page.page_number} in chapter {chapter.id}")

    async def load_page_pixmap(self, chapter: Chapter, page: Page) -> QPixmap:
        cache_id = page.local_path if page.local_path else page.remote_url
        if not cache_id:
            raise ValueError(f"Page {page.page_number} has no valid identifier")
        cached_pixmap = self.image_cache.get(cache_id)
        if cached_pixmap:
            return cached_pixmap

        image_bytes = await self.load_page_bytes(chapter, page)
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(image_bytes))
        if pixmap.isNull():
            raise ValueError(f"Failed to load image for page {page.page_number}")
        self.image_cache.put(cache_id, pixmap, save_to_disk=True)
        return pixmap

    async def prefetch_pages(self, chapter: Chapter, pages: list[Page], current_index: int, window: int = 2):
        start_idx = max(0, current_index - window)
        end_idx = min(len(pages), current_index + window + 1)
        for key in list(self._prefetch_tasks.keys()):
            if key not in [f"{chapter.id}_{i}" for i in range(start_idx, end_idx)]:
                task = self._prefetch_tasks.pop(key)
                if not task.done():
                    task.cancel()


        for idx in range(start_idx, end_idx):
            if idx == current_index:
                continue  
            page = pages[idx]
            task_key = f"{chapter.id}_{idx}"
            if task_key in self._prefetch_tasks:
                continue

            cache_id = page.local_path if page.local_path else page.remote_url
            if cache_id and self.image_cache.has(cache_id):
                continue

            task = asyncio.create_task(self._prefetch_page(chapter, page))
            self._prefetch_tasks[task_key] = task

    async def _prefetch_page(self, chapter: Chapter, page: Page):
        try:
            await self.load_page_pixmap(chapter, page)
        except Exception as e:

            print(f"Prefetch failed for page {page.page_number}: {e}")

    def cancel_prefetch(self):
        for task in self._prefetch_tasks.values():
            if not task.done():
                task.cancel()
        self._prefetch_tasks.clear()

    async def close(self):
        self.cancel_prefetch()
        for source in self._sources.values():
            if hasattr(source, 'close'):
                await source.close()

_global_loader: Optional[PageLoader] = None

def get_page_loader() -> PageLoader:
    global _global_loader
    if _global_loader is None:
        _global_loader = PageLoader()
    return _global_loader
