from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class Chapter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    manga_id: int = Field(foreign_key="manga.id", index=True)
    chapter_number: str  
    title: Optional[str] = None
    source: str = Field(default="local")  
    source_chapter_id: Optional[str] = None  
    is_downloaded: bool = Field(default=False)
    download_path: Optional[str] = None  
    page_count: int = Field(default=0)
    language: str = Field(default="en")
    scanlation_group: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    def __repr__(self):
        return f"Chapter(id={self.id}, manga_id={self.manga_id}, number={self.chapter_number})"
