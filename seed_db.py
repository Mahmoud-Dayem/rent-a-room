"""Load the sample rooms into database.db: python seed_db.py."""

import asyncio

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependicies.database import engine, init_db
from app.models.room import RoomModel
from rooms import rooms


async def seed_rooms() -> int:
    """Insert missing rooms and return the number added."""

    await init_db()

    async with AsyncSession(engine) as session:
        result = await session.exec(select(RoomModel.id))
        existing_ids = set(result.all())

        new_rooms = [
            RoomModel.model_validate(data)
            for data in rooms
            if data["id"] not in existing_ids
        ]

        session.add_all(new_rooms)

        await session.commit()

        return len(new_rooms)


if __name__ == "__main__":
    inserted = asyncio.run(seed_rooms())
    print(f"Inserted {inserted} rooms into database.db.")
