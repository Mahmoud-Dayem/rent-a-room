"""Load the sample rooms into database.db: python seed_db.py."""

from sqlmodel import Session, select

from database import engine, init_db
from model import Room
from rooms import rooms


def seed_rooms() -> int:
    """Insert missing rooms and return the number added."""
    init_db()

    with Session(engine) as session:
        existing_ids = set(session.exec(select(Room.id)).all())
        new_rooms = [
            Room.model_validate(data)
            for data in rooms
            if data["id"] not in existing_ids
        ]
        session.add_all(new_rooms)
        session.commit()
        return len(new_rooms)


if __name__ == "__main__":
    inserted = seed_rooms()
    print(f"Inserted {inserted} rooms into database.db.")
