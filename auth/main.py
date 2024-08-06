import os
from datetime import datetime, timedelta

import jwt
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from loguru import logger
from sqlalchemy.orm import Session, sessionmaker

from auth.crud import create_user
from auth.ldap import authenticate
from auth.models import engine, Base, User

app = FastAPI(title="AuthService")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@router.get("/verify_token")
async def verify_token(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    _logger = logger.bind(username=User.username)

    try:
        decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        user = db.query(User).filter(User.username == decoded_token["username"]).first()

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


@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    if not authenticate(form_data.username, form_data.password):
        logger.bind(user=form_data.username).error("Неудачная попытка войти в систему")
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    logger.bind(user=form_data.username).info("В систему вошел пользователь")

    token_data = {
        "username": form_data.username,
        "exp": datetime.utcnow() + timedelta(seconds=960),
    }
    access_token = jwt.encode(token_data, os.getenv("SECRET_KEY"), algorithm="HS256")

    user = create_user(form_data.username, access_token)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.bind(user=form_data.username).info("В базу данных добавлен новый пользователь")

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
    user = db.query(User).filter(User.username == decoded_token["username"]).first()

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


logger.add(
    "auth/logs/log.log",
    level="INFO",
    format="{time}  ||  {level.icon}{level}  ||  {function}  ||  {message} || {extra}",
    rotation="09:00",
    compression="zip",
    colorize=None,
)