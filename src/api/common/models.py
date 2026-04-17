from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CloudFile(BaseModel):
    """Универсальная модель файла для UI и логики приложения."""
    name: str
    path: str
    is_dir: bool
    size: int  # в байтах
    modified_at: Optional[datetime] = None
    mime_type: Optional[str] = None
    file_id: Optional[str] = None