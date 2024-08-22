from ldap3 import Server, Connection, SUBTREE, ALL
from dotenv import load_dotenv
import os

from models import Access, User, Role

load_dotenv()


def create_connection(user, user_password):
    server = Server('ldap://adv-fs.advengineering.ru', port=389, use_ssl=False, get_info=ALL)
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
    if user_name == "admin" and user_password == "admin":
        accesses = db.query(Access).all()
        accesses = [access.name for access in accesses]
        return True, accesses, "Admin"

    elif db.query(User).filter(User.username == user_name).first() and db.query(User).filter(User.password == user_password).first():
        user = db.query(User).filter(User.username == user_name).first()
        for role in user.roles:
            if db.query(Role).filter(Role.name == role).first():
                role = db.query(Role).filter(Role.name == role).first()
            else:
                raise ValueError('Role not found')
        accesses = role.role_accesses
        user_accesses = []
        for role in accesses:
            if accesses[role]:
                user_accesses.append(role)
        return True, user_accesses, role

    else:
        try:
            conn = create_connection('CN=Насибов Фариз,OU=External,DC=advengineering,DC=ru',
                                     os.getenv('LDAP_PASSWORD'))
            conn.bind()

            search_filter = f'(sAMAccountName={user_name})'
            conn.search(search_base='DC=advengineering,DC=ru',
                        search_filter=search_filter,
                        search_scope=SUBTREE,
                        attributes='userPrincipalName')

            return is_valid_credentials(conn, user_password), [], None

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

        finally:
            conn.unbind()
