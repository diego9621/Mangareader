from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Progress(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    manga_id: int = Field(foreign_key="manga.id", index=True)
    chapter_id: int = Field(foreign_key="chapter.id", index=True)
    page_index: int = Field(default=0)
    chapter_path: Optional[str] = Field(default=None, index=True)
    last_read: datetime = Field(default_factory=datetime.utcnow)
