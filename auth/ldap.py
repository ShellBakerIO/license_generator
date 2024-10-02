import os

from fastapi import HTTPException

import crud
import bcrypt
from dotenv import load_dotenv
from ldap3 import Server, Connection, SUBTREE, ALL

from models import Access, User, Role

load_dotenv()


def create_connection(user, user_password):
    server = Server(
        "ldap://adv-fs.advengineering.ru",
        port=389,
        use_ssl=False,
        get_info=ALL
    )
    conn = Connection(server, user=user, password=user_password)

    return conn


def get_user_cn(conn):
    user_info = conn.entries[0]
    cn = user_info.entry_dn

    return cn


def is_valid_credentials(conn, user_password):
    if conn.entries:
        cn = get_user_cn(conn)
        new_conn = create_connection(cn, user_password)
        return new_conn.bind()
    else:
        return False


def authenticate(user_name, user_password, db):
    private_key = crud.load_private_key()
    user_password = crud.decrypt_password(user_password, private_key)
    if user_name == "admin" and user_password == "admin":
        accesses = db.query(Access).all()
        accesses = [access.name for access in accesses]
        return True, accesses, "Admin"

    elif user := db.query(User).filter(User.username == user_name).first():
        if bcrypt.checkpw(user_password.encode("utf-8"),
                          user.password.encode("utf-8")):
            roles = db.query(Role).filter(Role.name.in_(user.roles)).all()
            accesses = [r.role_accesses for r in roles]
            user_accesses = []
            for role in roles:
                for access in role.role_accesses:
                    if role.role_accesses[access]:
                        user_accesses.append(access)
            return True, user_accesses, roles
        else:
            return False, [], None
    else:
        try:
            conn = create_connection(
                "CN=Насибов Фариз,OU=External,DC=advengineering,DC=ru",
                os.getenv("LDAP_PASSWORD"),
            )
            conn.bind()

            search_filter = f"(sAMAccountName={user_name})"
            conn.search(
                search_base="DC=advengineering,DC=ru",
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes="userPrincipalName",
            )

            return is_valid_credentials(conn, user_password), [], None

        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

        finally:
            conn.unbind()
