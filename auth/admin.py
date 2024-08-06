from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from models import SessionLocal, engine, Base
from schemas import User, UserCreate, Role, RoleCreate, Access, AccessCreate
import crud

Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/users/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)


@app.get("/roles/", response_model=List[Role])
def read_roles(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    roles = crud.get_roles(db, skip=skip, limit=limit)
    return roles


@app.post("/roles/", response_model=Role)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    return crud.create_role(db=db, role=role)


@app.get("/accesses/", response_model=List[Access])
def read_accesses(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    accesses = crud.get_accesses(db, skip=skip, limit=limit)
    return accesses


@app.post("/accesses/", response_model=Access)
def create_access(access: AccessCreate, db: Session = Depends(get_db)):
    return crud.create_access(db=db, access=access)
