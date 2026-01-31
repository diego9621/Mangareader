import aiohttp
import asyncio
from typing import Optional
from datetime import datetime
from .base import MangaSource, MangaMetadata, ChapterMetadata, PageInfo


class MangaDexSource(MangaSource):
    BASE_URL = "https://api.mangadex.org"
    CDN_URL = "https://uploads.mangadex.org"
    REQUEST_DELAY = 0.2  
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0
        self._lock = asyncio.Lock()

    @property
    def source_name(self) -> str:
        return "mangadex"

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _rate_limit(self):
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self.REQUEST_DELAY:
                await asyncio.sleep(self.REQUEST_DELAY - elapsed)
            self._last_request_time = asyncio.get_event_loop().time()

    async def _request(self, endpoint: str, params: dict = None) -> dict:
        await self._rate_limit()
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        async with session.get(url, params=params) as response:
            if response.status == 429:  
                retry_after = int(response.headers.get("X-RateLimit-Retry-After", 60))
                await asyncio.sleep(retry_after)
                return await self._request(endpoint, params)
            response.raise_for_status()
            return await response.json()

    def _parse_manga(self, data: dict) -> MangaMetadata:
        manga_id = data["id"]
        attributes = data["attributes"]
        title_obj = attributes.get("title", {})
        title = (
            title_obj.get("en") or
            title_obj.get("ja-ro") or
            list(title_obj.values())[0] if title_obj else "Unknown"
        )

        alt_titles = attributes.get("altTitles", [])
        title_english = None
        for alt in alt_titles:
            if "en" in alt:
                title_english = alt["en"]
                break


        desc_obj = attributes.get("description", {})
        description = desc_obj.get("en") or (list(desc_obj.values())[0] if desc_obj else None)
        cover_filename = None
        for rel in data.get("relationships", []):
            if rel["type"] == "cover_art":
                cover_filename = rel["attributes"]["fileName"]
                break

        cover_url = None
        if cover_filename:
            cover_url = f"{self.CDN_URL}/covers/{manga_id}/{cover_filename}.512.jpg"
        author = None
        artist = None
        for rel in data.get("relationships", []):
            if rel["type"] == "author":
                author = rel["attributes"].get("name")
            elif rel["type"] == "artist":
                artist = rel["attributes"].get("name")

        tags = []
        genres = []
        for tag in attributes.get("tags", []):
            tag_name = tag["attributes"]["name"].get("en", "")
            if tag_name:
                tags.append(tag_name)
                if tag["attributes"].get("group") == "genre":
                    genres.append(tag_name)

        return MangaMetadata(
            source="mangadex",
            source_id=manga_id,
            title=title,
            title_english=title_english,
            description=description,
            cover_url=cover_url,
            author=author,
            artist=artist,
            genres=genres,
            tags=tags,
            status=attributes.get("status"),  
            year=attributes.get("year")
        )

    async def search(self, query: str, page: int = 1, limit: int = 50) -> list[MangaMetadata]:
        params = {
            "title": query,
            "limit": min(limit, 100),  
            "offset": (page - 1) * limit,
            "includes[]": ["cover_art", "author", "artist"],
            "order[relevance]": "desc",
            "contentRating[]": ["safe", "suggestive", "erotica"],  
        }

        data = await self._request("/manga", params)
        return [self._parse_manga(manga) for manga in data.get("data", [])]

    async def get_manga(self, source_id: str) -> MangaMetadata:
        params = {
            "includes[]": ["cover_art", "author", "artist"]
        }
        data = await self._request(f"/manga/{source_id}", params)
        return self._parse_manga(data["data"])

    async def get_chapters(self, source_id: str, language: str = "en") -> list[ChapterMetadata]:
        all_chapters = []
        offset = 0
        limit = 100
        while True:
            params = {
                "manga": source_id,
                "translatedLanguage[]": [language],
                "limit": limit,
                "offset": offset,
                "order[chapter]": "asc",
                "includes[]": ["scanlation_group"],
                "contentRating[]": ["safe", "suggestive", "erotica"],
            }

            data = await self._request("/chapter", params)
            chapters = data.get("data", [])
            if not chapters:
                break
            for chapter in chapters:
                attrs = chapter["attributes"]
                scanlation_group = None
                for rel in chapter.get("relationships", []):
                    if rel["type"] == "scanlation_group":
                        scanlation_group = rel.get("attributes", {}).get("name")
                        break


                published_at = None
                if attrs.get("publishAt"):
                    try:
                        published_at = datetime.fromisoformat(attrs["publishAt"].replace("Z", "+00:00"))
                    except:
                        pass

                chapter_metadata = ChapterMetadata(
                    source_chapter_id=chapter["id"],
                    chapter_number=attrs.get("chapter", "0"),
                    title=attrs.get("title"),
                    language=attrs.get("translatedLanguage", language),
                    page_count=attrs.get("pages", 0),
                    scanlation_group=scanlation_group,
                    published_at=published_at,
                    volume=attrs.get("volume")
                )
                all_chapters.append(chapter_metadata)
            offset += limit

            if offset >= data.get("total", 0):
                break

        def chapter_sort_key(ch: ChapterMetadata):
            try:
                return float(ch.chapter_number)
            except ValueError:
                return 0

        all_chapters.sort(key=chapter_sort_key)
        return all_chapters

    async def get_pages(self, chapter_id: str) -> list[PageInfo]:
        data = await self._request(f"/at-home/server/{chapter_id}")
        base_url = data["baseUrl"]
        chapter_hash = data["chapter"]["hash"]
        filenames = data["chapter"]["data"]  
        pages = []
        for i, filename in enumerate(filenames):
            url = f"{base_url}/data/{chapter_hash}/{filename}"
            pages.append(PageInfo(
                page_number=i,
                url=url
            ))

        return pages

    async def download_image(self, url: str) -> bytes:
        await self._rate_limit()
        session = await self._get_session()
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.read()

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
