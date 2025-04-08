from datetime import datetime

from pydantic import Field, field_validator

from ....domain.models import Event


class EventCreate(Event):
    title: str = Field(..., min_length=1, max_length=100)
    description: str
    location: str
    start_time: datetime
    end_time: datetime
    created_by: str | None = Field(default=None, exclude=True)

    class Config:
        from_attributes = True


class EventUpdate(Event):
    title: str | None = Field(..., min_length=1, max_length=100)
    description: str | None = None
    location: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
