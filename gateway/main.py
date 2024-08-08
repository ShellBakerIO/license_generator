from typing import Annotated
from fastapi import Depends, FastAPI, APIRouter, File, UploadFile, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from dto.user import UserCreate, RoleCreate, AccessCreate
from dto.license import LicensesInfo

from api_wrapper import gateway_router


app = FastAPI()
api_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@gateway_router(api_router.post, "/token")
async def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    response: Response,
):
    pass


@gateway_router(api_router.get, "/users/me")
async def read_users_me(
    token: Annotated[str, Depends(oauth2_scheme)], request: Request, response: Response
):
    pass


@gateway_router(api_router.post, "/generate_license")
def generate_license(
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    lic: LicensesInfo = Depends(LicensesInfo.as_form),
    machine_digest_file: UploadFile = File(...),
):
    pass


@gateway_router(api_router.get, "/all_licenses")
def get_all_licenses(
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(api_router.get, "/license/{id}")
def find_license(
    id: int,
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(api_router.get, "/machine_digest_file/{id}")
def find_machine_digest(
    id: int,
    current_user: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
):
    pass


@gateway_router(api_router.get, "/users/")
def read_users(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 10,
):
    pass


@gateway_router(api_router.post, "/users/")
def create_user(
    request: Request,
    response: Response,
    user: UserCreate,
):
    pass


@gateway_router(api_router.get, "/roles/")
def read_roles(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 10,
):
    pass


@gateway_router(api_router.post, "/roles/")
def create_role(
    request: Request,
    response: Response,
    role: RoleCreate,
):
    pass


@gateway_router(api_router.get, "/accesses/")
def read_accesses(
    request: Request,
    response: Response,
    skip: int = 0,
    limit: int = 10,
):
    pass


@gateway_router(api_router.post, "/accesses/")
def create_access(
    request: Request,
    response: Response,
    access: AccessCreate,
):
    pass


app.include_router(api_router)
