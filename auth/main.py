import os
from datetime import datetime, timedelta
import jwt
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session, sessionmaker
from loguru import logger

from license.crud import create_user
from license.ldap import authenticate
from license.models import engine, User, Base

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
async def verify_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        user = db.query(User).filter(User.username == decoded_token["username"]).first()

        if user and decoded_token["exp"] > datetime.utcnow().timestamp():
            return {"username": user.username}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired or invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
    user = db.query(User).filter(User.username == decoded_token["username"]).first()

    if user and decoded_token["exp"] > datetime.utcnow().timestamp():
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
