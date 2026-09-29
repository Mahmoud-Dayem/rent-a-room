from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from model import Room

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})


def init_db():
    """Creates the database tables based on your SQLModel classes."""
    SQLModel.metadata.create_all(bind=engine)


def get_session():
    """Returns a configured SQLAlchemy session for use in FastAPI endpoints."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
