import asyncio
from typing import Annotated

from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import Session, SQLModel, create_engine

from app.models.booking import BookingModel
from app.models.room import RoomModel
from app.models.user import UserModel

sqlite_file_name = "database.db"
sqlite_url = f"sqlite+aiosqlite:///{sqlite_file_name}"

engine = create_async_engine(sqlite_url, echo=True)


@event.listens_for(engine.sync_engine, "connect")
def enable_foreign_keys(dpapi_connection, connection_record):
    dpapi_connection.execute("PRAGMA foreign_keys=ON")


async def init_db():

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async with AsyncSession(engine) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
