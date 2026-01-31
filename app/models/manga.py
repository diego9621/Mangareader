from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Manga(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    source: str = Field(default="local")  
    source_id: Optional[str] = None  
    cover_url: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    artist: Optional[str] = None
    genres: Optional[str] = None  
    tags: Optional[str] = None  
    status: Optional[str] = None  
    anilist_id: Optional[int] = None
    mal_id: Optional[int] = None
    mangadex_id: Optional[str] = None
    is_downloaded: bool = Field(default=False)
    download_path: Optional[str] = None  
    path: Optional[str] = None
    is_favorite: bool = Field(default=False)
    last_opened: Optional[datetime] = None
    open_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
