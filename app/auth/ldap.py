from ldap3 import Server, Connection, ALL, SUBTREE
from dotenv import load_dotenv
import os


def get_user_info_by_samaccountname(ldap_server, ldap_port, ldap_user, ldap_password, base_dn, samaccountname):
    try:
        server = Server(ldap_server, port=ldap_port, use_ssl=False, get_info=ALL)
        conn = Connection(server, user=ldap_user, password=ldap_password)
        conn.bind()

        search_filter = f'(sAMAccountName={samaccountname})'
        search_attributes = ['cn', 'givenName', 'sn', 'mail', 'memberOf']

        conn.search(search_base=base_dn, search_filter=search_filter, search_scope=SUBTREE, attributes=search_attributes)

        if conn.entries:
            user_info = conn.entries[0].entry_to_json()
            return user_info
        else:
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        conn.unbind()


if __name__ == '__main__':
    load_dotenv()

    ldap_server = 'ldap://adv-fs.advengineering.ru'
    ldap_port = 389
    ldap_user = 'CN=Насибов Фариз,OU=External,DC=advengineering,DC=ru'
    ldap_password = os.getenv('LDAP_PASSWORD')
    base_dn = 'DC=advengineering,DC=ru'
    samaccountname = 'f.nasibov'

    user_info = get_user_info_by_samaccountname(ldap_server, ldap_port, ldap_user, ldap_password, base_dn, samaccountname)
    print(user_info)


"""
Другой способ
from ldap3 import Server, Connection, SUBTREE, ALL_ATTRIBUTES
from app.auth.config import PASSWORD


def auth_ldap(password):
    s = Server('ldap://adv-fs.advengineering.ru', port=389, use_ssl=True, get_info=ALL)
    c = Connection(s, user='CN=Насибов Фариз,OU=External,DC=advengineering,DC=ru', password=password, auto_bind=True)

    b = c.search(search_base='DC=advengineering,DC=ru',
             search_filter='(CN=Насибов Фариз,OU=External,DC=advengineering,DC=ru)',
             search_scope=SUBTREE,
             attributes=ALL_ATTRIBUTES)

    res = c.response
    return b, res


print(auth_ldap(PASSWORD))
"""
