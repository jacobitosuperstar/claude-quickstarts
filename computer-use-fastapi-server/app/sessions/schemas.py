"""Pydantic schemas for session API."""
from datetime import datetime
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Request to create a new session."""

    # Screenshot storage configuration (optional)
    store_screenshots: bool = Field(default=False, description="Whether to store screenshots in database")
    screenshot_scale: Optional[int] = Field(default=2, ge=1, le=8, description="Scale divisor: 1=full, 2=half, 4=quarter")
    screenshot_quality: Optional[int] = Field(default=70, ge=10, le=100, description="JPEG quality (1-100)")


class SessionResponse(BaseModel):
    """Session information."""

    id: str
    created_at: datetime
    status: str
    store_screenshots: bool
    screenshot_scale: Optional[int]
    screenshot_quality: Optional[int]

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Request to send a message."""

    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    """Message information."""

    id: int
    session_id: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class StreamEvent(BaseModel):
    """WebSocket event during agent execution."""

    type: Literal["text", "tool_use", "tool_result", "thinking", "error", "completed"]
    content: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)
