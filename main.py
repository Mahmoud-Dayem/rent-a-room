from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from rooms import rooms

app = FastAPI(title="Rent Room")


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "Welcome to Rent-a-Room!"}


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


class Room(BaseModel):
    id: int
    name: str
    price_per_night: float
    bedrooms: int
    bathrooms: int
    area: float


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
