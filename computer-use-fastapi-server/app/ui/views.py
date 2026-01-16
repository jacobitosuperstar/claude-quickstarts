"""UI views for rendering HTML templates."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_session as get_db
from app.sessions import services

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/ui", tags=["ui"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Homepage - list all sessions."""
    sessions = services.list_sessions(db)
    return templates.TemplateResponse(
        "sessions_list.html",
        {"request": request, "sessions": sessions}
    )


@router.post("/sessions/create")
async def create_session_ui(db: Session = Depends(get_db)):
    """Create a new session and redirect to it."""
    session = services.create_session(db)
    return RedirectResponse(url=f"/ui/sessions/{session.id}", status_code=303)


@router.get("/sessions/{session_id}", response_class=HTMLResponse)
async def session_detail(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db)
):
    """Session detail page with chat and VNC."""
    session = services.get_session(db, session_id)
    if not session:
        return RedirectResponse(url="/ui/")

    # Get messages and parse them for display
    messages_raw = services.get_messages(db, session_id)
    messages = []

    for msg in messages_raw:
        import json
        try:
            content_json = json.loads(msg.content)
            msg_type = "assistant"

            # Determine message type and format content
            if content_json.get("role") == "user":
                msg_type = "user"
                content = content_json.get("text", "")
            elif content_json.get("type") == "text":
                content = content_json.get("text", "")
            elif content_json.get("type") == "thinking":
                msg_type = "thinking"
                content = f"[Thinking] {content_json.get('thinking', '...')}"
            elif content_json.get("type") == "tool_use":
                msg_type = "tool"
                content = f"🔧 Tool: {content_json.get('name')}\nInput: {json.dumps(content_json.get('input'), indent=2)}"
            elif content_json.get("type") == "tool_result":
                msg_type = "tool"
                output = content_json.get("output", "No output")
                error = content_json.get("error", "")
                content = f"✓ Tool Result\n{error if error else output}"
            else:
                content = json.dumps(content_json, indent=2)

            messages.append({"type": msg_type, "content": content})
        except:
            messages.append({"type": "assistant", "content": msg.content})

    return templates.TemplateResponse(
        "session_detail.html",
        {"request": request, "session": session, "messages": messages}
    )
