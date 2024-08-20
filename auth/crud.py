from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from models import User, Role, Access
from schemas import UserCreate, RoleCreate, AccessCreate


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
    return db.query(User).all()


def create_user(db: Session, user: UserCreate):
    db_user = User(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_roles(db: Session):
    roles = db.query(Role).all()
    return roles


def create_role(db: Session, role: RoleCreate):
    db_role = Role(name=role.name, role_accesses=generate_access_dict(db, role_id=None))
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def add_role_to_user(db: Session, user_id: int, role_id: int, added: bool):
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


def create_access(db: Session, access: AccessCreate):
    db_access = Access(name=access.name)
    db.add(db_access)
    db.commit()
    db.refresh(db_access)
    return db_access


def edit_access_for_role(db: Session, role_id: int, access_id: int, has_access: bool):
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
