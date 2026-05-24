"""Player state schemas."""

from typing import Any

from pydantic import BaseModel, Field


class StatePatchRequest(BaseModel):
    op: str = Field(description="append | remove | set | inc | merge")
    value: Any = None


class StateValueResponse(BaseModel):
    key: str
    value: Any


class StateAllResponse(BaseModel):
    items: dict[str, Any]
