from typing import Annotated
from fastapi import Depends, FastAPI, APIRouter, File, UploadFile, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth.admin import get_db
from auth.schemas import UserCreate, RoleCreate, AccessCreate
from dto.license import LicensesInfo

from api_wrapper import router


app = FastAPI()
api_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router(api_router.post, '/token')
async def get_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request, response: Response):
    pass


@router(api_router.get, '/users/me')
async def read_users_me(token: Annotated[str, Depends(oauth2_scheme)], request: Request, response: Response):
    pass


@router(api_router.post, '/generate_license')
def generate_license(current_user: Annotated[str, Depends(oauth2_scheme)],
                     request: Request, response: Response,
                     lic: LicensesInfo = Depends(LicensesInfo.as_form),
                     machine_digest_file: UploadFile = File(...)):
    pass


@router(api_router.get, '/all_licenses')
def get_all_licenses(current_user: Annotated[str, Depends(oauth2_scheme)],request: Request, response: Response):
    pass


@router(api_router.get, "/license/{id}")
def find_license(id: int, current_user: Annotated[str, Depends(oauth2_scheme)],request: Request, response: Response):
    pass


@router(api_router.get, "/machine_digest_file/{id}")
def find_machine_digest(id: int, current_user: Annotated[str, Depends(oauth2_scheme)], request: Request, response: Response):
    pass


@router(api_router.get, "/users/")
def read_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    request: Request,
    response: Response,
):
    pass


@router(api_router.post, "/users/")
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    request: Request,
    response: Response,
):
    pass


@router(api_router.get, "/roles/")
def read_roles(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    request: Request,
    response: Response,
):
    pass


@router(api_router.post, "/roles/")
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    request: Request,
    response: Response,
):
    pass


@router(api_router.get, "/accesses/")
def read_accesses(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    request: Request,
    response: Response,
):
    pass


@router(api_router.post, "/accesses/")
def create_access(
    access: AccessCreate,
    db: Session = Depends(get_db),
    request: Request,
    response: Response,
):
    pass


app.include_router(api_router)
