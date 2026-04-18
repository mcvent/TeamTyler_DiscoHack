from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CloudFile(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    modified_at: Optional[datetime] = None
    mime_type: Optional[str] = None
    file_id: Optional[str] = None