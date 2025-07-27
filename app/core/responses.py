from typing import Any, Optional

from pydantic import BaseModel

class StandardResponse(BaseModel):
    """Envelope for API responses."""

    code: int
    message: str
    data: Optional[Any] = None


def success(data: Any = None, message: str = "Success", code: int = 200) -> StandardResponse:
    """Return a standardized success response."""
    return StandardResponse(code=code, message=message, data=data)
