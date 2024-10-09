import base64
import os
import re
from typing import List

import bcrypt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from models import User, Role, Access
from schemas import UserCreate, RoleCreate, UserBase

load_dotenv()


def create_accesses(db):
    if db.query(Access).filter(Access.name == "READ_LICENSE").first() is None:
        read_license = Access(name=os.getenv("READ_LICENSE"))
        create_license = Access(name=os.getenv("CREATE_LICENSE"))
        retrieve_file = Access(name=os.getenv("RETRIEVE_FILE"))
        user_role_management = Access(name=os.getenv("USER_ROLE_MANAGEMENT"))
        all = [read_license, create_license, retrieve_file,
               user_role_management]
        db.add_all(all)
        db.commit()
        db.refresh(read_license)
        db.refresh(create_license)
        db.refresh(retrieve_file)
        db.refresh(user_role_management)


def add_authorized_user_in_db(user: UserBase, role: List[str], db):
    admin_email = "admin@admin.com"
    user_db = db.query(User).filter(User.username == user.login).first()
    if user.username == "admin" and user_db is None:
        user = User(username=user.username, email=admin_email,
                    password=user.password, roles=[role])
        db.add(user)
        db.commit()
        db.refresh(user)
    elif user_db is None:
        user = User(username=user.login, email=user.email,
                    password=user.password, roles=role)
        db.add(user)
        db.commit()
        db.refresh(user)


def load_public_key():
    public_key_data = os.getenv("PUBLIC_KEY")
    if not public_key_data:
        raise HTTPException(status_code=404,
                            detail="Public key not found in environment variables")

    try:
        public_key = serialization.load_pem_public_key(
            public_key_data.encode("utf-8"),
            backend=default_backend()
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return public_key


def load_private_key():
    private_key_data = os.getenv("PRIVATE_KEY")
    if not private_key_data:
        raise HTTPException(status_code=404,
                            detail="Private key not found in environment variables")

    try:
        private_key = serialization.load_pem_private_key(
            private_key_data.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        return private_key
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def decrypt_password(encrypted_password: str, private_key):
    try:
        encrypted_password_bytes = base64.b64decode(encrypted_password)
        decrypted_password = private_key.decrypt(
            encrypted_password_bytes,
            padding.PKCS1v15()
        )
        return decrypted_password.decode('utf-8')
    except Exception as e:
        return encrypted_password


def hash_password(password: str):
    try:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=401,
                            detail=f"Failed to hash password: {e}")


def generate_access_dict(db: Session, role_id: int | None = None,
                         access_id: int | None = None,
                         has_access: bool = False):
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
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=409, detail="User already exists")

    private_key = load_private_key()
    decrypted_password = decrypt_password(user.password, private_key)
    hashed_password = hash_password(decrypted_password)

    pattern = r"^\S+@\S+\.\S+$"
    match = re.fullmatch(pattern, user.email)

    db_user = User(username=user.username, email=user.email,
                   password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, id: int):
    user = db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if os.getenv('USER_ROLE_MANAGEMENT') in user.roles:
        raise HTTPException(status_code=403,
                            detail="You are not allowed to delete this user")

    db.delete(user)
    db.commit()
    return user


def get_roles(db: Session):
    roles = db.query(Role).all()
    return roles


def create_role(db: Session, role: RoleCreate):
    if db.query(Role).filter(Role.name == role.name).first():
        raise HTTPException(status_code=409, detail="Role already exists")

    db_role = Role(name=role.name,
                   role_accesses=generate_access_dict(db, role_id=None))
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
        raise HTTPException(status_code=404, detail="User not found")
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

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


def change_role_accesses(db: Session, role_id: int, access_id: int,
                         has_access: bool):
    role = db.query(Role).filter(Role.id == role_id).first()
    access = db.query(Access).filter(Access.id == access_id).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if not access:
        raise HTTPException(status_code=404, detail="Access not found")

    role.role_accesses = generate_access_dict(db, role_id, access_id,
                                              has_access)

    flag_modified(role, "role_accesses")
    db.commit()
    db.refresh(role)

    return role
