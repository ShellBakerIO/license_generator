from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")

DB_HOST_TEST = os.environ.get("DB_HOST_TEST")
DB_PORT_TEST = os.environ.get("DB_PORT_TEST")
DB_NAME_TEST = os.environ.get("DB_NAME_TEST")
DB_USER_TEST = os.environ.get("DB_USER_TEST")
DB_PASS_TEST = os.environ.get("DB_PASS_TEST")

READ_LICENSE = os.environ.get("READ_LICENSE")
CREATE_LICENSE = os.environ.get("CREATE_LICENSE")
RETRIEVE_FILE = os.environ.get("RETRIEVE_FILE")
USER_ROLE_MANAGEMENT = os.environ.get("USER_ROLE_MANAGEMENT")

LDAP_PASSWORD = os.environ.get("LDAP_PASSWORD")
