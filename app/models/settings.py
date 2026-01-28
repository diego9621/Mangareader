from sqlmodel import SQLModel, Field

class Settings(SQLModel, table=True):
    id: int | None = Field(default=1, primary_key=True)
    library_root: str