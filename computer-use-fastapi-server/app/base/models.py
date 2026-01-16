from typing_extensions import TypedDict
from datetime import datetime


class TestResponse(TypedDict):
    now: datetime
