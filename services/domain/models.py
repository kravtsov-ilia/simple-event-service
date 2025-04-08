from enum import Enum

from beanie import Document
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal


class Topics(str, Enum):
    created = 'created'
    updated = 'updated'
    deleted = 'deleted'


class EventInfo(BaseModel):
    id: str
    title: str
    action: Topics
    user: str
    timestamp: str


class Event(Document):
    title: str = Field(..., min_length=1, max_length=100)
    description: str
    location: str
    start_time: datetime
    end_time: datetime
    created_by: str | None = Field(default=None, exclude=True)
    tags: list[str] | None = None
    max_attendees: int | None = None
    status: str | None = "scheduled"
    attachment_url: str | None = None
    coordinates: tuple[float, float] | None = None


    @field_validator("end_time")
    @classmethod
    def end_time_after_start_time(cls, v, values):
        if "start_time" in values.data and v <= values.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    @field_validator("start_time")
    @classmethod
    def start_time_cannot_be_in_past(cls, v):
        if v < datetime.now():
            raise ValueError("start_time cannot be in the past")
        return v

    class Settings:
        name = "events"


class Notification(Document):
    type: Literal["notification"]
    notification_type: str
    event: EventInfo
    user: str
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "notifications"

class User(Document):
    username: str
    email: str
    password: str
    full_name: str | None = None
    is_verified: bool = False


    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        # TODO improve
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v


    class Settings:
        name = "users"
        indexes = [
            "username",
            "email",
        ]