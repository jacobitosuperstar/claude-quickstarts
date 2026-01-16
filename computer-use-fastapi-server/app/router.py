from fastapi.routing import APIRouter
from app.base.views import router as base_router
from app.sessions.views import router as sessions_router
from app.ui.views import router as ui_router


api_router: APIRouter = APIRouter()
api_router.include_router(base_router)
api_router.include_router(sessions_router)
api_router.include_router(ui_router)
