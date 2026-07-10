

from typing import Any, Generic, TypeVar
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic.generics import GenericModel  # pydantic v1 compat shim not needed in v2

T = TypeVar("T")


# ── Envelope schema (for Swagger docs) ────────────────────────────

class ApiResponse(BaseModel):
   
    success: bool
    message: str
    data: Any = None

def ok(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
) -> JSONResponse:
    """200 OK with data."""
    return JSONResponse(
        status_code=status_code,
        content=_body(True, message, data),
    )


def created(
    data: Any = None,
    message: str = "Created successfully",
) -> JSONResponse:
    """201 Created with data."""
    return JSONResponse(
        status_code=201,
        content=_body(True, message, data),
    )


def no_data(
    message: str = "Success",
    status_code: int = 200,
) -> JSONResponse:
    """200 with no payload — e.g. logout, delete."""
    return JSONResponse(
        status_code=status_code,
        content=_body(True, message, None),
    )


def error(
    message: str,
    status_code: int = 400,
    detail: Any = None,
) -> JSONResponse:
    """Error response — used by the global handler."""
    return JSONResponse(
        status_code=status_code,
        content=_body(False, message, detail),
    )


# ── Internal helper ────────────────────────────────────────────────

def _serialize(obj: Any) -> Any:
    """
    Recursively serialize pydantic models, UUIDs, datetimes, etc.
    to JSON-safe primitives so JSONResponse can encode them.
    """
    from datetime import datetime
    from uuid import UUID
    from pydantic import BaseModel as PydanticBase

    if isinstance(obj, PydanticBase):
        return obj.model_dump(mode="json")
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (UUID,)):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def _body(success: bool, message: str, data: Any) -> dict:
    return {
        "success": success,
        "message": message,
        "data": _serialize(data),
    }
