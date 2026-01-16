"""Business logic for agent session management."""
import asyncio
import base64
import io
import json
import uuid
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session
from fastapi import WebSocket

from .models import Session as SessionModel, Message as MessageModel
from .schemas import SessionCreate
from computer_use_demo.loop import sampling_loop, APIProvider
from computer_use_demo.tools import ToolResult
from anthropic.types.beta import BetaContentBlockParam


# Track active agent tasks and their message buffers for concurrent execution
active_sessions: Dict[str, Dict] = {}  # {session_id: {"task": Task, "buffer": list, "db": Session}}


def resize_screenshot(base64_image: str, scale: int, quality: int) -> str:
    """Resize and compress a base64 screenshot using integer scaling."""
    try:
        from PIL import Image

        # Decode base64 image
        image_data = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_data))

        # Apply integer scaling (1=full, 2=half, 4=quarter, etc.)
        if scale > 1:
            width, height = image.size
            new_size = (width // scale, height // scale)
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to JPEG and compress
        buffer = io.BytesIO()
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        image.save(buffer, format='JPEG', quality=quality, optimize=True)

        # Encode back to base64
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except ImportError:
        # PIL not installed, return original
        return base64_image
    except Exception:
        # Any error, return original
        return base64_image


def create_session(db: Session, session_data: Optional[SessionCreate] = None) -> SessionModel:
    """Create a new session with optional screenshot configuration."""
    session = SessionModel(
        id=str(uuid.uuid4()),
        status="active",
        store_screenshots=session_data.store_screenshots if session_data else False,
        screenshot_scale=session_data.screenshot_scale if session_data else 2,
        screenshot_quality=session_data.screenshot_quality if session_data else 70,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> Optional[SessionModel]:
    """Get session by ID."""
    return db.query(SessionModel).filter(SessionModel.id == session_id).first()


def list_sessions(db: Session) -> list[SessionModel]:
    """List all sessions."""
    return db.query(SessionModel).order_by(SessionModel.created_at.desc()).all()


def get_messages(db: Session, session_id: str) -> list[MessageModel]:
    """Get all messages for a session."""
    return (
        db.query(MessageModel)
        .filter(MessageModel.session_id == session_id)
        .order_by(MessageModel.created_at.asc())
        .all()
    )


def add_message(db: Session, session_id: str, content: str) -> MessageModel:
    """Add a message to a session."""
    message = MessageModel(session_id=session_id, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def finish_session(db: Session, session_id: str) -> Optional[SessionModel]:
    """Mark a session as finished/inactive."""
    session = get_session(db, session_id)
    if not session:
        return None

    # Cancel any running agent task
    if session_id in active_sessions:
        cancel_agent_task(session_id)

    session.status = "finished"
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, session_id: str) -> bool:
    """Delete a session and all its messages."""
    session = get_session(db, session_id)
    if not session:
        return False

    # Cancel any running agent task
    if session_id in active_sessions:
        cancel_agent_task(session_id)

    # Delete messages first (cascade should handle this, but being explicit)
    db.query(MessageModel).filter(MessageModel.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return True


async def run_agent(
    session_id: str,
    message: str,
    db: Session,
    websocket: Optional[WebSocket] = None,
    api_key: Optional[str] = None,
):
    """Run the computer use agent loop."""
    from app.settings import settings

    session = get_session(db, session_id)
    if not session:
        return

    session.status = "running"
    db.commit()

    messages = [{"role": "user", "content": [{"type": "text", "text": message}]}]

    # Use provided API key or fall back to settings
    api_key_to_use = api_key or settings.anthropic_api_key
    if not api_key_to_use:
        raise ValueError("No Anthropic API key provided")

    # Buffer for batch inserts - store in active_sessions for cleanup on disconnect
    pending_messages = []
    if session_id in active_sessions:
        active_sessions[session_id]["buffer"] = pending_messages
        active_sessions[session_id]["db"] = db

    def flush_messages():
        """Flush pending messages to database."""
        if pending_messages:
            db.bulk_insert_mappings(MessageModel, pending_messages)
            db.commit()
            pending_messages.clear()

    try:
        async def output_callback(content: BetaContentBlockParam):
            # Stream to WebSocket immediately
            if websocket:
                await websocket.send_json({
                    "type": content.get("type", "text"),
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat(),
                })

            # Add to buffer for batch insert
            if isinstance(content, dict):
                pending_messages.append({
                    "session_id": session_id,
                    "content": json.dumps(content),
                    "created_at": datetime.utcnow()
                })

                # Flush when buffer reaches configured size
                if len(pending_messages) >= settings.message_batch_size:
                    flush_messages()

        async def tool_output_callback(tool_result: ToolResult, tool_id: str):
            # Stream to WebSocket immediately
            if websocket:
                await websocket.send_json({
                    "type": "tool_result",
                    "content": {"tool_id": tool_id, "output": tool_result.output, "error": tool_result.error},
                    "timestamp": datetime.utcnow().isoformat(),
                })

            # Build content for storage
            content_data = {
                "type": "tool_result",
                "tool_id": tool_id,
                "output": tool_result.output,
                "error": tool_result.error
            }

            # Optionally store screenshot if session has it enabled
            if session.store_screenshots and tool_result.base64_image:
                resized_image = resize_screenshot(
                    tool_result.base64_image,
                    session.screenshot_scale or 2,
                    session.screenshot_quality or 70
                )
                content_data["screenshot"] = resized_image

            # Add to buffer for batch insert
            pending_messages.append({
                "session_id": session_id,
                "content": json.dumps(content_data),
                "created_at": datetime.utcnow()
            })

            # Flush when buffer reaches configured size
            if len(pending_messages) >= settings.message_batch_size:
                flush_messages()

        def api_response_callback(request, response, error):
            pass

        # Store initial user message
        pending_messages.append({
            "session_id": session_id,
            "content": json.dumps({"type": "text", "text": message, "role": "user"}),
            "created_at": datetime.utcnow()
        })

        await sampling_loop(
            model="claude-sonnet-4-5-20250929",
            provider=APIProvider.ANTHROPIC,
            system_prompt_suffix="",
            messages=messages,
            output_callback=output_callback,
            tool_output_callback=tool_output_callback,
            api_response_callback=api_response_callback,
            api_key=api_key_to_use,
            only_n_most_recent_images=3,
            max_tokens=4096,
            tool_version="computer_use_20250124",
            thinking_budget=None,
            token_efficient_tools_beta=False,
        )

        # Flush any remaining messages
        flush_messages()

        session.status = "completed"
        db.commit()

        if websocket:
            await websocket.send_json({
                "type": "completed",
                "content": {"message": "Task completed"},
                "timestamp": datetime.utcnow().isoformat(),
            })

    except asyncio.CancelledError:
        # Task was cancelled (WebSocket disconnect) - flush messages and mark as cancelled
        flush_messages()
        session.status = "cancelled"
        db.commit()
        raise  # Re-raise to properly cancel the task

    except Exception as e:
        # Flush any remaining messages before marking as error
        flush_messages()

        session.status = "error"
        db.commit()

        if websocket:
            await websocket.send_json({
                "type": "error",
                "content": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat(),
            })

    finally:
        # Cleanup: remove from active sessions
        if session_id in active_sessions:
            del active_sessions[session_id]


def start_agent_task(
    session_id: str,
    message: str,
    db: Session,
    websocket: Optional[WebSocket] = None,
    api_key: str = None,
) -> asyncio.Task:
    """Start agent as background task for concurrent execution."""
    task = asyncio.create_task(run_agent(session_id, message, db, websocket, api_key))
    active_sessions[session_id] = {"task": task, "buffer": [], "db": db}
    return task


def cancel_agent_task(session_id: str):
    """Cancel an active agent task and flush its messages."""
    if session_id in active_sessions:
        session_data = active_sessions[session_id]
        task = session_data["task"]
        buffer = session_data["buffer"]
        db = session_data["db"]

        # Cancel the task
        task.cancel()

        # Flush any pending messages
        if buffer:
            db.bulk_insert_mappings(MessageModel, buffer)
            db.commit()
            buffer.clear()
