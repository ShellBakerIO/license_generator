import os
from datetime import datetime, timedelta
from typing import List

import jwt
from fastapi import FastAPI, Depends
from fastapi import HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

import crud
from ldap import authenticate
from models import SessionLocal, engine, Base, Access, User, Role
import schemas

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
    if db.query(Access).filter(Access.name == "READ_LICENSE").first() is None:
        read_license = Access(name=os.getenv("READ_LICENSE"))
        create_license = Access(name=os.getenv("CREATE_LICENSE"))
        retrieve_file = Access(name=os.getenv("RETRIEVE_FILE"))
        user_role_management = Access(name=os.getenv("USER_ROLE_MANAGEMENT"))
        db.add_all([read_license, create_license, retrieve_file, user_role_management])
        db.commit()
        db.refresh(read_license)
        db.refresh(create_license)
        db.refresh(retrieve_file)
        db.refresh(user_role_management)
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth, accesses, role = authenticate(form_data.username, form_data.password, db)

    if auth:
        logger.bind(user=form_data.username).info("В систему вошел пользователь")
        claims = accesses

        token_data = {
            "sub": form_data.username,
            "exp": datetime.utcnow() + timedelta(hours=3),
            "claims": claims,
        }

        access_token = jwt.encode(token_data, os.getenv("SECRET_KEY"), algorithm="HS256")

        if db.query(User).filter(User.username == "admin").first() is None:
            user = User(username=form_data.username, roles=[role])
            db.add(user)
            db.commit()
            db.refresh(user)
        elif db.query(User).filter(User.username == form_data.username).first() is None:
            user = User(username=form_data.username, roles=[])
            db.add(user)
            db.commit()
            db.refresh(user)

        return {
            "access_token": access_token,
            "token_type": "Bearer",
        }

    else:
        logger.bind(user=form_data.username).error("Неудачная попытка войти в систему")
        raise HTTPException(status_code=400, detail="Incorrect username or password")


@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        if decoded_token["exp"] >= datetime.utcnow().timestamp():
            logger.bind(username=decoded_token["sub"]).info("Токен пользователя валиден")
            return {
                "sub": decoded_token["sub"],
                "valid": True
            }
    except jwt.ExpiredSignatureError:
        logger.bind(username=decoded_token["sub"]).error("Токен пользователя истек")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        logger.bind(username=decoded_token["sub"]).error("Токен не найден")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@app.get("/users/", response_model=List[schemas.User])
def read_users(db: Session = Depends(get_db)):
    users = crud.get_users(db)
    logger.info("Выведен список пользователей")
    return users


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info("Добавлен новый пользователь")
    return crud.create_user(db=db, user=user)


@app.delete("/users/", response_model=schemas.User)
def delete_user(user: schemas.UserDelete, db: Session = Depends(get_db)):
    user = db.get(User, user.id)
    db.delete(user)
    db.commit()
    logger.info("Пользователь удален")
    return user


@app.get("/roles/", response_model=List[schemas.Role])
def read_roles(db: Session = Depends(get_db)):
    roles = crud.get_roles(db)
    logger.info("Выведен список ролей")
    return roles


@app.post("/roles/", response_model=schemas.Role)
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
    logger.info("Добавлена новая роль")
    return crud.create_role(db=db, role=role)


@app.delete("/roles/", response_model=schemas.Role)
def delete_role(role: schemas.RoleDelete, db: Session = Depends(get_db)):
    role = db.get(Role, role.id)
    print(role)
    db.delete(role)
    db.commit()
    logger.info("Роль удалена")
    return role


@app.patch("/users/{user_id}/", response_model=schemas.User)
def add_role_to_user(role_to_user: schemas.Role_to_User, db: Session = Depends(get_db)):
    try:
        user = crud.add_role_to_user(db=db,
                                     user_id=role_to_user.user_id,
                                     role_id=role_to_user.role_id,
                                     added=role_to_user.added)
        logger.info(f"Роль с ID {role_to_user.role_id} добавлена пользователю с ID {role_to_user.user_id}")
        return user
    except ValueError as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/accesses/", response_model=List[schemas.Access])
def read_accesses(db: Session = Depends(get_db)):
    accesses = crud.get_accesses(db)
    logger.info("Выведен список доступов")
    return accesses


@app.patch("/roles/{role_id}/", response_model=schemas.Role)
def edit_access_for_role(access_to_role: schemas.Access_to_Role, db: Session = Depends(get_db)):
    try:
        role = crud.edit_access_for_role(db=db,
                                         role_id=access_to_role.role_id,
                                         access_id=access_to_role.access_id,
                                         has_access=access_to_role.has_access)
        logger.info(f"Доступ с ID {access_to_role.access_id} добавлен к роли с ID {access_to_role.role_id}")
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
