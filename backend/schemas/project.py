from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ProjectCreateRequest(BaseModel):
    collection_id: UUID
    name: str
    shard_user_list: Optional[List[str]] = None


class ProjectResponse(BaseModel):
    id: UUID
    collection_id: UUID
    user_id: UUID
    name: Optional[str]
    shard_user_list: Optional[List]
    selected_image_number: int
    total_image_number: int
    total_video_number: int
    marketing_letter_key: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
