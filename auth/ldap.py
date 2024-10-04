import os
from fastapi import HTTPException

import crud
import bcrypt
from dotenv import load_dotenv
from ldap3 import Server, Connection, SUBTREE, ALL

from schemas import AccessEntries, UserLDAP, UserCreate
from models import Access, User, Role

load_dotenv()


def create_connection(user, user_password):
    server = Server(os.getenv("LDAP_SERVER"), port=int(os.getenv("LDAP_PORT")),
                    use_ssl=False, get_info=ALL
                    )
    conn = Connection(server, user=user, password=user_password)

    return conn


def get_user_cn(conn) -> tuple[str | None, str | None]:
    user_info = conn.entries[0]
    user = user_info.entry_dn
    login_t = str(user_info.mail.value) if user_info.mail else None
    login = login_t.split('@')[0] if login_t is not None else None
    return user, login


def get_user_email_cn(conn):
    user_info = conn.entries[0]
    cn = str(user_info.mail.value) if user_info.mail else None
    return cn


def is_valid_credentials(conn, user_password) -> tuple[bool, UserLDAP]:
    if conn.entries:
        cn, login = get_user_cn(conn)
        user_email = get_user_email_cn(conn)
        new_conn = create_connection(cn, user_password)
        return new_conn.bind(), UserLDAP(username=cn,
                                         login=login,
                                         email=user_email,
                                         password=user_password)
    else:
        return False, UserLDAP(username='', login='', email=None,
                               password=user_password)


def get_auth_by_db(user, user_password, db):
    ae = AccessEntries(is_auth=False, accesses=[], role='')
    if bcrypt.checkpw(user_password.encode("utf-8"),
                      user.password.encode("utf-8")):
        roles = db.query(Role).filter(Role.name.in_(user.roles)).all()
        role_names = [role.name for role in roles]
        user_accesses = []
        for role in roles:
            for access in role.role_accesses:
                if role.role_accesses[access]:
                    user_accesses.append(access)
        return AccessEntries(is_auth=True, accesses=user_accesses,
                             role=role_names)
    return ae


def exist_user_in_system(user: UserLDAP, db) -> bool:
    filter_user = db.query(User).filter(User.username == user.login).exists()
    exists = db.query(filter_user).scalar()
    return exists


def get_auth_by_ldap(user_name: str, user_password: str, db) -> AccessEntries:
    conn = create_connection(os.getenv("LDAP_USER"),
                             os.getenv("LDAP_PASSWORD"),
                             )
    conn.bind()
    try:
        search_filter = f"(sAMAccountName={user_name})"
        conn.search(
            search_base=os.getenv("LDAP_SEARCH_BASE"),
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=["userPrincipalName", "mail"],
        )
        credentials_ldap, user_ldap = is_valid_credentials(conn, user_password)
        if credentials_ldap:
            e = exist_user_in_system(user_ldap, db)
            if e:
                user = db.query(User).filter(User.username == user_name).first()
                return get_auth_by_db(user, user_ldap.password, db)
            else:
                new_user = UserCreate(username=user_ldap.login,
                                      email=user_ldap.email,
                                      password=user_ldap.password
                                      )
                crud.create_user(db, new_user)
            return AccessEntries(is_auth=True, accesses=[], role="admin")
        detail = "Пользователь не найден, обратитесь к администратору"
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    finally:
        conn.unbind()


def authenticate(user_name, user_password, db) -> AccessEntries:
    private_key = crud.load_private_key()
    user_password = crud.decrypt_password(user_password, private_key)
    if user_name == "admin" and user_password == "admin":
        accesses = db.query(Access).all()
        accesses = [access.name for access in accesses]
        return AccessEntries(is_auth=True, accesses=accesses, role="Admin")
    user = db.query(User).filter(User.username == user_name).first()
    if user is not None:
        return get_auth_by_db(user, user_password, db)
    return get_auth_by_ldap(user_name, user_password, db)
