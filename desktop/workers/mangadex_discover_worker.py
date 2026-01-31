from PySide6.QtCore import QObject, Signal, QRunnable
import asyncio
from qasync import asyncSlot
from app.sources.mangadex import MangaDexSource


class MangadexDiscoverSignals(QObject):
    done = Signal(list, str)


class MangadexDiscoverWorker(QRunnable):
    def __init__(self, mode: str, query: str, signals: MangadexDiscoverSignals, page: int = 1, per_page: int = 50):
        super().__init__()
        self.mode = mode
        self.query = query
        self.signals = signals
        self.page = page
        self.per_page = per_page

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._fetch())
                self.signals.done.emit(result, "")
            finally:
                loop.close()
        except Exception as e:
            self.signals.done.emit([], str(e))

    async def _fetch(self):
        async with MangaDexSource() as source:
            if self.mode == "search":
                metadata_list = await source.search(self.query, self.page, self.per_page)
            else:
                metadata_list = await source.search("", self.page, self.per_page)

            result = []
            for meta in metadata_list:
                item = {
                    "id": meta.source_id,
                    "mangadex_id": meta.source_id,
                    "title": {
                        "english": meta.title_english or meta.title,
                        "romaji": meta.title,
                        "native": meta.title_native
                    },
                    "description": meta.description,
                    "coverImage": {
                        "large": meta.cover_url
                    },
                    "status": meta.status,
                    "author": meta.author,
                    "artist": meta.artist,
                    "genres": meta.genres or [],
                    "tags": [{"name": tag} for tag in (meta.tags or [])],
                    "averageScore": None,
                    "meanScore": int(meta.rating) if meta.rating else None,
                    "popularity": None,
                    "favourites": None,
                    "chapters": None,
                    "volumes": None,
                    "startDate": {"year": meta.year} if meta.year else {},
                    "endDate": {},
                    "season": None,
                    "seasonYear": None,
                    "format": "MANGA",
                    "anilist_id": meta.anilist_id,
                    "mal_id": meta.mal_id,
                    "siteUrl": f"https://mangadex.org/title/{meta.source_id}",
                    "source": "mangadex"
                }
                result.append(item)

            return result
