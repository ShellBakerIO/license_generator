from ldap3 import Server, Connection, SUBTREE, ALL
from dotenv import load_dotenv
import os


load_dotenv()


def get_user_info_by_username(user_name, user_password):
    try:
        server = Server('ldap://adv-fs.advengineering.ru', port=389, use_ssl=False, get_info=ALL)
        conn = Connection(server, user='CN=Насибов Фариз,OU=External,DC=advengineering,DC=ru', password=os.getenv('LDAP_PASSWORD'))
        conn.bind()
        search_filter = f'(sAMAccountName={user_name})'

        conn.search(search_base='DC=advengineering,DC=ru', search_filter=search_filter, search_scope=SUBTREE, attributes='userPrincipalName')

        if conn.entries:
            user_info = conn.entries[0]
            cn = user_info.entry_dn
            new_conn = Connection(server, user=cn, password=user_password)
            return new_conn.bind()
        else:
            return False

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    finally:
        conn.unbind()
