from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class MangaMetadata:
    source: str
    source_id: str
    title: str
    title_english: Optional[str] = None
    title_native: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    author: Optional[str] = None
    artist: Optional[str] = None
    genres: list[str] = None
    tags: list[str] = None
    status: Optional[str] = None 
    year: Optional[int] = None
    rating: Optional[float] = None
    anilist_id: Optional[int] = None
    mal_id: Optional[int] = None
    
    def __post_init__(self):
        if self.genres is None:
            self.genres = []
        if self.tags is None:
            self.tags = []

@dataclass
class ChapterMetadata:
    source_chapter_id: str
    chapter_number: str
    title: Optional[str] = None
    language: str = "en"
    page_count: int = 0
    scanlation_group: Optional[str] = None
    published_at: Optional[datetime] = None
    volume: Optional[str] = None


@dataclass
class PageInfo:
    page_number: int
    url: str
    width: Optional[int] = None
    height: Optional[int] = None


class MangaSource(ABC):    
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass
    
    @abstractmethod
    async def search(self, query: str, page: int = 1, limit: int = 50) -> list[MangaMetadata]:
        pass
    
    @abstractmethod
    async def get_manga(self, source_id: str) -> MangaMetadata:
        pass
    
    @abstractmethod
    async def get_chapters(self, source_id: str, language: str = "en") -> list[ChapterMetadata]:
        pass
    
    @abstractmethod
    async def get_pages(self, chapter_id: str) -> list[PageInfo]:
        pass
    
    @abstractmethod
    async def download_image(self, url: str) -> bytes:
        pass
