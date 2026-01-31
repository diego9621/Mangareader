from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class DownloadQueue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    manga_id: Optional[int] = Field(foreign_key="manga.id")
    chapter_id: Optional[int] = Field(foreign_key="chapter.id")
    status: str = Field(default="pending")  
    priority: int = Field(default=0)  
    progress_percent: float = Field(default=0.0)
    downloaded_pages: int = Field(default=0)
    total_pages: int = Field(default=0)
    error_message: Optional[str] = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    def __repr__(self):
        return f"DownloadQueue(id={self.id}, chapter_id={self.chapter_id}, status={self.status})"
