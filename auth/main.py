import os
from datetime import datetime, timedelta
from typing import List, Annotated

import jwt
from fastapi import FastAPI, Depends
from fastapi import HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from loguru import logger
from sqlalchemy.orm import Session

import crud
from ldap import authenticate
from models import SessionLocal, User as UserModel, engine, Base
from schemas import User, UserCreate, Role, RoleCreate, Access, AccessCreate

app = FastAPI(title="AdminService")
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
Base.metadata.create_all(bind=engine)


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
            headers={"WWW-Authenticate": "Bearer"})

    decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
    user = db.get(UserModel, decoded_token["username"])

    if (user is not None) and (decoded_token["exp"] < datetime.utcnow()):
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"})


@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()

    if user and jwt.decode(user.token, os.getenv("SECRET_KEY"), algorithms=["HS256"])["exp"] > datetime.utcnow().timestamp():
        return {
            "access_token": user.token,
            "token_type": "bearer",
        }

    if not authenticate(form_data.username, form_data.password):
        logger.bind(user=form_data.username).error("Неудачная попытка войти в систему")
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    logger.bind(user=form_data.username).info("В систему вошел пользователь")

    token_data = {
        "username": form_data.username,
        "exp": datetime.utcnow() + timedelta(seconds=960),
    }
    access_token = jwt.encode(token_data, os.getenv("SECRET_KEY"), algorithms=["HS256"])

    user = crud.register_user(db, form_data.username, access_token)

    logger.bind(user=form_data.username).info(
        "В базу данных добавлен новый пользователь"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/users/me")
async def read_users_me(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    _logger = logger.bind(username=User.username)
    decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
    user = db.query(UserModel).filter(UserModel.username == decoded_token["username"]).first()

    if user and decoded_token["exp"] > datetime.utcnow().timestamp():
        _logger.info("Токен пользователя валиден")
        return user
    else:
        _logger.error("Токен пользователя не обнаружен или истек")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/verify_token")
async def verify_token(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    _logger = logger.bind(username=User.username)

    try:
        decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        user = db.query(UserModel).filter(UserModel.username == decoded_token["username"]).first()

        if user and decoded_token["exp"] > datetime.utcnow().timestamp():
            _logger.info("Токен пользователя валиден")
            return {"username": user.username}
        else:
            _logger.error("Токен пользователя не обнаружен или истек")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired or invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        _logger.error("Токен пользователя истек")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        _logger.error("Несуществующий токен")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/users/", response_model=List[User])
def read_users(db: Session = Depends(get_db)):
    users = crud.get_users(db)
    return users


@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    token_data = {
        "username": user.username,
        "exp": datetime.utcnow() + timedelta(seconds=960),
    }
    access_token = jwt.encode(token_data, os.getenv("SECRET_KEY"), algorithm="HS256")

    return crud.create_user(db=db, user=user, token=access_token)


@app.get("/roles/", response_model=List[Role])
def read_roles(db: Session = Depends(get_db)):
    roles = crud.get_roles(db)
    return roles


@app.post("/roles/", response_model=Role)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    return crud.create_role(db=db, role=role)


@app.get("/accesses/", response_model=List[Access])
def read_accesses(db: Session = Depends(get_db)):
    accesses = crud.get_accesses(db)
    return accesses


@app.post("/accesses/", response_model=Access)
def create_access(access: AccessCreate, db: Session = Depends(get_db)):
    return crud.create_access(db=db, access=access)


logger.add(
    "auth/logs/log.log",
    level="INFO",
    format="{time}  ||  {level.icon}{level}  ||  {function}  ||  {message} || {extra}",
    rotation="09:00",
    compression="zip",
    colorize=None,
)
