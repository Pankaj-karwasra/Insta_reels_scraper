from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Reel(BaseModel):
    id: str
    reel_url: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    posted_at: Optional[datetime] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None


class ScrapeResponse(BaseModel):
    username: str
    scraped_at: datetime
    count: int
    reels: List[Reel]