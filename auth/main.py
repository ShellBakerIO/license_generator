import os
from datetime import datetime, timedelta, timezone
from typing import List

import jwt
from fastapi import FastAPI, Depends
from fastapi import HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy.orm import Session

import crud
import schemas
from ldap import authenticate
from models import SessionLocal, engine, Base

app = FastAPI(title="AdminService")
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    crud.create_accesses(db)
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: Session = Depends(get_db)):
    authenticate_obj = authenticate(form_data.username,
                                        form_data.password, db)
    auth = authenticate_obj.is_auth
    accesses = authenticate_obj.accesses
    if auth:
        username = form_data.username
        logger.bind(user=username).info("В систему вошел пользователь")
        claims = accesses

        token_data = {
            "sub": username,
            "exp": datetime.now(timezone.utc) + timedelta(hours=3),
            "claims": claims,
        }
        access_token = jwt.encode(token_data, os.getenv("SECRET_KEY"),
                                  algorithm="HS256")
        return {
            "access_token": access_token,
            "token_type": "Bearer",
        }

    else:
        msg = "Неудачная попытка войти в систему"
        logger.bind(user=form_data.username).error(msg)
        raise HTTPException(status_code=400,
                            detail="Incorrect username or password")


@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    username = "Unknown user"
    try:
        decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"),
                                   algorithms=["HS256"])
        username = decoded_token.get("sub", "Unknown user")
        logger.bind(username=username).info("Токен пользователя валиден")
        return {
            "sub": username,
            "valid": True
        }
    except jwt.ExpiredSignatureError:
        logger.bind(username=username).error("Токен пользователя истек")
        raise HTTPException(status_code=401, detail="Token expired")
    except (jwt.PyJWTError, jwt.DecodeError):
        logger.bind(username=username).error("Токен не найден")
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/public_key")
def read_public_key():
    public_key = os.getenv("PUBLIC_KEY")
    return public_key


@app.get("/users", response_model=List[schemas.User])
def read_users(db: Session = Depends(get_db)):
    users = crud.get_users(db)
    logger.info("Выведен список пользователей")
    return users


@app.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info("Добавлен новый пользователь")
    return crud.create_user(db=db, user=user)


@app.delete("/users{id}", response_model=schemas.User)
def delete_user(id: int, db: Session = Depends(get_db)):
    user = crud.delete_user(db=db, id=id)
    logger.info("Пользователь удален")
    return user


@app.get("/roles", response_model=List[schemas.Role])
def read_roles(db: Session = Depends(get_db)):
    roles = crud.get_roles(db)
    logger.info("Выведен список ролей")
    return roles


@app.post("/roles", response_model=schemas.Role)
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
    logger.info("Добавлена новая роль")
    return crud.create_role(db=db, role=role)


@app.delete("/roles/{role_id}", response_model=schemas.Role)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = crud.delete_role(db=db, id=role_id)
    logger.info("Роль удалена")
    return role


@app.patch("/users/{user_id}", response_model=schemas.User)
def change_user_role(role_to_user: schemas.Role_to_User,
                     db: Session = Depends(get_db)):
    try:
        user = crud.change_user_role(db=db,
                                     user_id=role_to_user.user_id,
                                     role_id=role_to_user.role_id,
                                     added=role_to_user.added)
        logger.info(
            f"Роль с ID {role_to_user.role_id} добавлена пользователю с ID {role_to_user.user_id}")
        return user
    except ValueError as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accesses", response_model=List[schemas.Access])
def read_accesses(db: Session = Depends(get_db)):
    accesses = crud.get_accesses(db)
    logger.info("Выведен список доступов")
    return accesses


@app.patch("/roles/{role_id}", response_model=schemas.Role)
def change_role_accesses(access_to_role: schemas.Access_to_Role,
                         db: Session = Depends(get_db)):
    try:
        access_id = access_to_role.access_id
        role_id = access_to_role.role_id
        has_access = access_to_role.has_access
        role = crud.change_role_accesses(db=db, role_id=role_id,
                                         access_id=access_id,
                                         has_access=has_access)

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
