from dataclasses import dataclass
from typing import Optional
from datetime import datetime


# Domain Models
@dataclass
class Message:
    """Domain entity: Represents a chat message"""
    id: str
    content: str
    formatted: str  # kivy markup version of content if present
    message_type: str  # "text" or "image"
    image_path: Optional[str] = None
    role: str = "user" # user, assistant, system, status
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

