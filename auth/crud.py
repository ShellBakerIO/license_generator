import os
import re

import bcrypt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from models import User, Role, Access
from schemas import UserCreate, RoleCreate

load_dotenv()


def load_private_key():
    private_key_data = os.getenv("PRIVATE_KEY")
    private_key = serialization.load_pem_private_key(
        private_key_data.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    return private_key


def decrypt_password(encrypted_password: str, private_key):
    decrypted_password = private_key.decrypt(
        encrypted_password,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_password.decode('utf-8')


def hash_password(password: str):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def generate_access_dict(db: Session, role_id: int | None = None, access_id: int | None = None, has_access: bool = False):
    all_accesses = db.query(Access).all()
    role = db.query(Role).filter(Role.id == role_id).first()
    access_dict = {}

    for access in all_accesses:
        if access_id == access.id:
            access_dict[access.name] = has_access
        elif role_id is None:
            access_dict[access.name] = False
        elif access.name in role.role_accesses:
            access_dict[access.name] = role.role_accesses[access.name]
        else:
            access_dict[access.name] = False

    return access_dict


def get_users(db: Session):
    users = db.query(User).all()
    return users


def create_user(db: Session, user: UserCreate):
    if True:
        db_user = User(username=user.username, email=user.email, password=user.password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    private_key = load_private_key()
    decrypted_password = decrypt_password(user.password, private_key)
    hashed_password = hash_password(decrypted_password)
    user.password = hashed_password

    pattern = r"^\S+@\S+\.\S+$"
    match = re.fullmatch(pattern, user.email)

    db_user = User(username=user.username, email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, id: int):
    user = db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return user


def get_roles(db: Session):
    roles = db.query(Role).all()
    return roles


def create_role(db: Session, role: RoleCreate):
    db_role = Role(name=role.name, role_accesses=generate_access_dict(db, role_id=None))
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def delete_role(db: Session, id: int):
    role = db.get(Role, id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    db.delete(role)
    db.commit()
    return role


def change_user_role(db: Session, user_id: int, role_id: int, added: bool):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()

    if not user:
        raise ValueError(f"Пользователя с ID {user_id} не существует")
    if not role:
        raise ValueError(f"Роли с ID {role_id} не существует")

    if user.roles is None:
        user.roles = []

    if added:
        if role.name not in user.roles:
            user.roles.append(str(role.name))
    else:
        if role.name in user.roles:
            user.roles.remove(str(role.name))

    flag_modified(user, "roles")
    db.commit()
    db.refresh(user)

    return user


def get_accesses(db: Session):
    return db.query(Access).all()


def change_role_accesses(db: Session, role_id: int, access_id: int, has_access: bool):
    role = db.query(Role).filter(Role.id == role_id).first()
    access = db.query(Access).filter(Access.id == access_id).first()

    if not role:
        raise ValueError("Роль не найдена")
    if not access:
        raise ValueError("Доступ не найден")

    role.role_accesses = generate_access_dict(db, role_id, access_id, has_access)

    flag_modified(role, "role_accesses")
    db.commit()
    db.refresh(role)

    return role
