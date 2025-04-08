from pydantic import BaseModel, Field

from services.domain.models import User


class SimpleUser(BaseModel):
    id: str
    username: str

class UserResponse(User):
    id: str
    password: str | None = Field(default=None, exclude=True)
