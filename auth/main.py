import os
from datetime import datetime, timedelta
from typing import List, Annotated

import jwt
from fastapi import FastAPI, Depends
from fastapi import HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from loguru import logger
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

import crud
from ldap import authenticate
from models import SessionLocal, engine, Base
from schemas import User, UserCreate, Role, RoleCreate, Access, AccessCreate

app = FastAPI(title="AdminService")
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])

        if decoded_token["exp"] >= datetime.utcnow().timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired or invalid",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return decoded_token["username"]

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):

    if authenticate(form_data.username, form_data.password):
        logger.bind(user=form_data.username).info("В систему вошел пользователь")

        token_data = {
            "username": form_data.username,
            "exp": datetime.utcnow() + timedelta(hours=3)
        }

        access_token = jwt.encode(token_data, os.getenv("SECRET_KEY"), algorithm="HS256")

        return {
            "access_token": access_token,
            "token_type": "Bearer",
        }

    else:
        logger.bind(user=form_data.username).error("Неудачная попытка войти в систему")
        raise HTTPException(status_code=400, detail="Incorrect username or password")


@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
    _logger = logger.bind(username=decoded_token["username"])

    if decoded_token["exp"] >= datetime.utcnow().timestamp():
        _logger.info("Токен пользователя валиден")
        return decoded_token["username"]
    else:
        _logger.error("Токен пользователя не обнаружен или истек")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/verify_token")
async def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        return {"username": decoded_token["username"], "valid": True}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@app.get("/users/", response_model=List[User])
def read_users(db: Session = Depends(get_db)):
    users = crud.get_users(db)
    logger.info("Выведен список пользователей")
    return users


@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info("Добавлен новый пользователь")
    return crud.create_user(db=db, user=user)


@app.get("/roles/", response_model=List[Role])
def read_roles(db: Session = Depends(get_db)):
    roles = crud.get_roles(db)
    logger.info("Выведен список ролей")
    return roles


@app.post("/roles/", response_model=Role)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    logger.info("Добавлена новая роль")
    return crud.create_role(db=db, role=role)


@app.patch("/users/{user_id}/", response_model=User)
def add_role_to_user(user_id: int, role_id: int, added: bool, db: Session = Depends(get_db)):
    try:
        user = crud.add_role_to_user(db=db, user_id=user_id, role_id=role_id, added=added)
        logger.info(f"Роль с ID {role_id} добавлена пользователю с ID {user_id}")
        return user
    except ValueError as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accesses/", response_model=List[Access])
def read_accesses(db: Session = Depends(get_db)):
    accesses = crud.get_accesses(db)
    logger.info("Выведен список доступов")
    return accesses


@app.post("/accesses/", response_model=Access)
def create_access(access: str, db: Session = Depends(get_db)):
    logger.info("Добавлен новый доступ")
    return crud.create_access(db=db, access=access)


@app.patch("/roles/{role_id}/", response_model=Role)
def edit_access_for_role(role_id: int, access_id: int, has_access: bool, db: Session = Depends(get_db)):
    try:
        role = crud.edit_access_for_role(db=db, role_id=role_id, access_id=access_id, has_access=has_access)
        logger.info(f"Доступ с ID {access_id} добавлен к роли с ID {role_id}")
        return role
    except ValueError as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))


logger.add(
    "/auth/logs/log.log",
    level="INFO",
    format="{time}  ||  {level.icon}{level}  ||  {function}  ||  {message} || {extra}",
    rotation="09:00",
    compression="zip",
    colorize=None,
)
