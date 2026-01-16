"""SQLAlchemy models for session management."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import DeclarativeBase


class Session(DeclarativeBase):
    """Agent session model."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="active")  # active, running, completed, error, cancelled

    # Screenshot storage configuration (per-session)
    store_screenshots: Mapped[bool] = mapped_column(Boolean, default=False)
    screenshot_scale: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=2)  # 1=full, 2=half, 4=quarter
    screenshot_quality: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=70)  # JPEG quality 1-100


class Message(DeclarativeBase):
    """Chat message model."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
