# from contextlib import asynccontextmanager
# from typing import Annotated, Literal, Optional

# from fastapi import (
#     APIRouter,
#     Cookie,
#     Depends,
#     FastAPI,
#     Header,
#     HTTPException,
#     Path,
#     Query,
#     Response,
#     status,
# )
# from fastapi.templating import Jinja2Templates
# from pydantic import BaseModel, Field
# from sqlmodel import col, select

# from app.dependicies.database import SessionDep, get_session, init_db
# from app.models.room import Room as RoomModel
# from app.models.room import RoomCreate, RoomUpdate

# routers = APIRouter(prefix="")


# @routers.get("/rooms", status_code=status.HTTP_200_OK, response_model=list[RoomModel])
# def root(session: SessionDep):
#     return session.exec(select(RoomModel)).all()
