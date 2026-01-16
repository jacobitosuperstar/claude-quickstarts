"""API endpoints for session management."""
from typing import List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session as get_db
from .schemas import SessionCreate, SessionResponse, MessageCreate, MessageResponse
from . import services


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse)
def create_session(
    session_data: SessionCreate = None,
    db: Session = Depends(get_db)
):
    """Create a new agent session with optional screenshot configuration."""
    session = services.create_session(db, session_data)
    return session


@router.get("/", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    """List all sessions."""
    sessions = services.list_sessions(db)
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get session by ID."""
    session = services.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
def get_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages for a session."""
    messages = services.get_messages(db, session_id)
    return messages


@router.patch("/{session_id}/finish", response_model=SessionResponse)
def finish_session(session_id: str, db: Session = Depends(get_db)):
    """Mark a session as finished/inactive."""
    session = services.finish_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a session and all its messages."""
    success = services.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}


@router.websocket("/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time agent interaction."""
    await websocket.accept()

    # Get a database session
    from app.database import SessionLocal
    db = SessionLocal()

    try:
        # Check if session exists
        session = services.get_session(db, session_id)
        if not session:
            await websocket.send_json({"type": "error", "content": {"error": "Session not found"}})
            await websocket.close()
            return

        # Wait for user message
        data = await websocket.receive_json()
        message = data.get("message", "")

        if not message:
            await websocket.send_json({"type": "error", "content": {"error": "No message provided"}})
            await websocket.close()
            return

        # Get API key from message or environment
        api_key = data.get("api_key") or None

        # Start agent task
        task = services.start_agent_task(session_id, message, db, websocket, api_key)

        # Wait for task completion
        await task

    except WebSocketDisconnect:
        # User disconnected - cancel the agent task and flush messages
        services.cancel_agent_task(session_id)
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "content": {"error": str(e)}})
        except:
            pass  # WebSocket might be closed
    finally:
        db.close()
