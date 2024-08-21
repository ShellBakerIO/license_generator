import os
from typing import Annotated
from fastapi import Depends, FastAPI, File, UploadFile, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from dto.license import LicensesInfo
from dto.user import UserCreate, RoleCreate, Access_to_Role, Role_to_User
from fastapi.middleware.cors import CORSMiddleware

from api_wrapper import gateway_router

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Content-Disposition"],
    expose_headers={"Content-Disposition"},
)


@gateway_router(app.post,
                "/token",
                payload_key='form_data',
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level=None,
                )
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/users/me",
                payload_key=None,
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level=None,
                )
async def read_users_me(
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.post,
                "/generate_license",
                payload_key='generate_license',
                service_url=os.environ.get('LICENSE_SERVICE_URL'),
                access_level="CREATE_LICENSE",
                )
async def generate_license(
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    lic: LicensesInfo = Depends(LicensesInfo.as_form),
    machine_digest_file: UploadFile = File(...),
):
    pass


@gateway_router(app.get,
                "/all_licenses",
                payload_key=None,
                service_url=os.environ.get('LICENSE_SERVICE_URL'),
                access_level="READ_LICENSE",
                )
async def get_all_licenses(
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/license/{id}",
                payload_key=None,
                service_url=os.environ.get('LICENSE_SERVICE_URL'),
                access_level="RETRIEVE_FILE",
                )
async def find_license(
    id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/machine_digest_file/{id}",
                payload_key=None,
                service_url=os.environ.get('LICENSE_SERVICE_URL'),
                access_level="RETRIEVE_FILE",
                )
def find_machine_digest(
    id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/users/",
                payload_key=None,
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level="USER_ROLE_MANAGEMENT",
                )
def read_users(
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.post,
                "/users/",
                payload_key='user',
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level="USER_ROLE_MANAGEMENT",
                )
def create_user(
    user: UserCreate,
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.delete,
                "/users/",
                payload_key='id',
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level="USER_ROLE_MANAGEMENT",
                )
def delete_user(
    id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/roles/",
                payload_key=None,
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level="USER_ROLE_MANAGEMENT",
                )
def read_roles(
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.post,
                "/roles/",
                payload_key='role',
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level="USER_ROLE_MANAGEMENT",
                )
def create_role(
    role: RoleCreate,
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.delete,
                "/roles/",
                payload_key='id',
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level="USER_ROLE_MANAGEMENT",
                )
def delete_role(
    id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.patch,
                "/users/{user_id}/",
                payload_key='role_to_user',
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level="USER_ROLE_MANAGEMENT",
                )
async def add_role_to_user(
    role_to_user: Role_to_User,
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/accesses/",
                payload_key=None,
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level="USER_ROLE_MANAGEMENT",
                )
def read_accesses(
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.patch, "/roles/{role_id}/",
                payload_key='access_to_role',
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                access_level="USER_ROLE_MANAGEMENT",
                )
async def edit_access_for_role(
    access_to_role: Access_to_Role,
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass
