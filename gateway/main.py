import os
from typing import Annotated, List
from fastapi import Depends, FastAPI, File, UploadFile, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from dto.user import UserCreate, RoleCreate, AccessCreate
from dto.license import LicensesInfo
from starlette.middleware.cors import CORSMiddleware

from api_wrapper import gateway_router
import dto

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@gateway_router(app.post,
                "/token",
                payload_key='form_data',
                service_url=os.environ.get('AUTH_SERVICE_URL'))
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/users/me",
                payload_key=None,
                service_url=os.environ.get('AUTH_SERVICE_URL'))
async def read_users_me(
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.post,
                "/generate_license",
                payload_key=None,
                service_url=os.environ.get('LICENSE_SERVICE_URL'))
async def generate_license(
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    lic: LicensesInfo = Depends(LicensesInfo.as_form),
    machine_digest_file: UploadFile = File(...),
):
    pass


@gateway_router(app.get,
                "/all_licenses",
                payload_key=None,
                service_url=os.environ.get('LICENSE_SERVICE_URL'))
async def get_all_licenses(

    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/license/{id}",
                payload_key=None,
                service_url=os.environ.get('LICENSE_SERVICE_URL'))
async def find_license(
    id: int,
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/machine_digest_file/{id}",
                payload_key=None,
                service_url=os.environ.get('LICENSE_SERVICE_URL'))
def find_machine_digest(
    id: int,
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/users/",
                payload_key=None,
                service_url=os.environ.get('AUTH_SERVICE_URL'))
def read_users(
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.post,
                "/users/",
                payload_key='user',
                service_url=os.environ.get('AUTH_SERVICE_URL'))
def create_user(
    user: UserCreate,
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/roles/",
                payload_key=None,
                service_url=os.environ.get('AUTH_SERVICE_URL'))
def read_roles(
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.post,
                "/roles/",
                payload_key='role',
                service_url=os.environ.get('AUTH_SERVICE_URL'))
def create_role(
    role: RoleCreate,

    request: Request,
    response: Response,
):
    pass


@gateway_router(app.patch,
                "/users/{user_id}/",
                payload_key=None,
                service_url=os.environ.get('AUTH_SERVICE_URL'))
async def add_role_to_user(
    user_id: int,
    role_id: int,
    added: bool,
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.get,
                "/accesses/",
                payload_key=None,
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                )
def read_accesses(
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(app.post,
                "/accesses/",
                payload_key='access',
                service_url=os.environ.get('AUTH_SERVICE_URL'),
                )
async def create_access(
    access: str,

    request: Request,
    response: Response,
):
    pass


@gateway_router(app.patch, "/roles/{role_id}/",
                payload_key=None,
                service_url=os.environ.get('AUTH_SERVICE_URL')

                )
async def edit_access_for_role(
    role_id: int,
    access_id: int,
    has_access: bool,

    request: Request,
    response: Response,
):
    pass
