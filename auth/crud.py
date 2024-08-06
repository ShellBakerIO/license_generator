from sqlalchemy.orm import Session
from models import User, Role, Access
from schemas import UserCreate, RoleCreate, AccessCreate


def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate):
    db_user = User(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_roles(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Role).offset(skip).limit(limit).all()


def create_role(db: Session, role: RoleCreate):
    db_role = Role(name=role.name)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def get_accesses(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Access).offset(skip).limit(limit).all()


def create_access(db: Session, access: AccessCreate):
    db_access = Access(name=access.name)
    db.add(db_access)
    db.commit()
    db.refresh(db_access)
    return db_access
