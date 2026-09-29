from contextlib import asynccontextmanager
from typing import Annotated, Literal, Optional

from fastapi import Cookie, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlmodel import select

from database import SessionDep, get_session, init_db
from model import Room as RoomModel
from rooms import rooms


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan, title="Rent Room")


class PreferenceCookies(BaseModel):
    theme: Literal["dark", "light"] = "light"
    lang: Literal["eng", "fr", "italy"] = "eng"


class UserAgent(BaseModel):
    user_agent: str | None = None


@app.get("/", status_code=status.HTTP_200_OK, response_model=list[RoomModel])
def root(session: SessionDep):
    return session.exec(select(RoomModel)).all()


# @app.get("/rooms", status_code=status.HTTP_200_OK)
# async def get_rooms(search: str = Query(None)):

#     if search:
#         filtered_rooms = [
#             room for room in rooms if search.lower() in room["name"].lower()
#         ]

#         return filtered_rooms

#     return rooms


@app.get("/rooms/faq")
async def get_rooms_faq():
    return {
        "check_in": "Check-in starts at 3 PM.",
        "check_out": "Check-out is before 11 AM.",
        "pets_allowed": False,
        "wifi_available": True,
    }


@app.get("/rooms/{room_id}")
async def get_room(room_id: int):
    for room in rooms:
        if room["id"] == room_id:
            return room
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")


max_price_query = Query(gt=10, le=10000)
annotated_max_price = Annotated[float | None, max_price_query]


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price_per_night: float = Field(ge=0)
    bedrooms: int = Field(ge=0)
    bathroom: int = Field(ge=0)
    area: float = Field(gt=0)


@app.post("/rooms", status_code=status.HTTP_201_CREATED, response_model=RoomModel)
def create_room(room: RoomCreate, session: SessionDep):
    db_room = RoomModel.model_validate(room)
    session.add(db_room)
    session.commit()
    session.refresh(db_room)
    return db_room


class RoomQuery(BaseModel):
    search: str | None = None
    max_price: float | None = Field(default=None, gt=10, le=10000)


# app.mount("/assets", StaticFiles(directory="assets"), name="assets")
@app.get("/rooms", status_code=status.HTTP_200_OK)
async def get_rooms(query: Annotated[RoomQuery, Query()]):
    if query.search and query.max_price is not None:
        filtered_rooms = [
            room
            for room in rooms
            if query.search.lower() in room["name"].lower()
            and room["price_per_night"] <= query.max_price
        ]

        return filtered_rooms

    return rooms


@app.get("/preference")
def set_preferences(response: Response):

    cookies_reference = PreferenceCookies()

    response.set_cookie(key="theme", value=cookies_reference.theme, max_age=86400)
    response.set_cookie(key="lang", value=cookies_reference.lang, max_age=86400)
    return {"message": "Cookies have been set"}
