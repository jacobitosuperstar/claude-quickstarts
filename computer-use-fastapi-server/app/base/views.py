import datetime
from fastapi import APIRouter

from .models import TestResponse


router: APIRouter = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("/")
def ping() -> TestResponse:
    """Checking the health of the server.
    """
    return TestResponse(now=datetime.datetime.now())
