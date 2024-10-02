"""
from collections.abc import Generator
import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.auth.models import engine, Licenses
import app


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
        statement = delete(Licenses)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
"""