from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Annotated

import jwt
from aio_pika import connect_robust
from beanie import init_beanie
from bson import ObjectId
from fastapi import FastAPI, Depends, HTTPException, status, Body, Request, Response
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from slowapi import Limiter

from .core.security import get_current_user

from .external.rabbitmq import publish_message
from .schemas.event import EventCreate, EventUpdate
from .schemas.user import SimpleUser, UserResponse
from ...domain.models import Event, EventInfo, Topics, User
from ...settings.conf import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(database=mongo_client.notification_db, document_models=[Event, User])

    rabbitmq_connection = await connect_robust(settings.RABBIT_URI)
    channel = await rabbitmq_connection.channel()

    app.state.rabbitmq_connection = rabbitmq_connection
    app.state.rabbitmq_channel = channel

    yield


def get_remote_address(request: Request) -> str:
    return request.client.host

app = FastAPI(lifespan=lifespan)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user: User):
    existing_user = await User.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_dict = user.model_dump(exclude={"id"})
    user_dict["password"] = pwd_context.hash(user.password)
    user_dict["is_verified"] = False

    result = await User(**user_dict).create()

    return UserResponse(
        id=str(result.id),
        **user_dict
    )


@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, email: Annotated[str, Body(...)], password: Annotated[str, Body(...)]):
    user = await User.find_one({"email": email})
    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(
        data={"sub": user.username, "email": user.email, "user_id": str(user.id)}
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/events", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate, user: SimpleUser = Depends(get_current_user)):
    data = event.model_dump()
    data['created_by'] = user.username

    event_doc = Event(**event.model_dump(), created_by=user.username)
    await event_doc.create()

    await publish_message(
        channel=app.state.rabbitmq_channel,
        message=EventInfo(
            id=str(event_doc.id),
            title=event_doc.title,
            action=Topics.created,
            user=user.username,
            timestamp=datetime.now().isoformat()
        ).model_dump()
    )

    return event_doc

@app.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str, user: SimpleUser = Depends(get_current_user)):
    event = await Event.get(ObjectId(event_id))
    if event:
        return event
    raise HTTPException(status_code=404, detail="Event not found")


@app.patch("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_data: EventUpdate, user: SimpleUser = Depends(get_current_user)):
    event = await Event.get(ObjectId(event_id))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for field, value in event_data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    await event.save()
    await publish_message(
        channel=app.state.rabbitmq_channel,
        message=EventInfo(
            id=str(event.id),
            title=event.title,
            action=Topics.updated,
            user=user.username,
            timestamp=datetime.now().isoformat()
        ).model_dump()
    )
    return event


@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: str, user: SimpleUser = Depends(get_current_user)):
    event = await Event.get(ObjectId(event_id))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await event.delete()
    await publish_message(
        channel=app.state.rabbitmq_channel,
        message=EventInfo(
            id=str(event.id),
            title=event.title,
            action=Topics.deleted,
            user=user.username,
            timestamp=datetime.now().isoformat()
        ).model_dump()
    )


@app.get("/events", response_model=List[Event])
async def list_events(skip: int = 0, limit: int = 10):
    events = await Event.find_all().skip(skip).limit(limit).to_list()
    return events

@app.get("/health")
async def health():
    return Response(status_code=200)
