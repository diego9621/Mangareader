from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Manga(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    path: str
    is_favorite: bool = Field(default=False)
    last_opened: Optional[datetime] = None
    open_count: int = Field(default=0)
    