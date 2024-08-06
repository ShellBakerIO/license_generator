from typing import Annotated
from fastapi import Depends, FastAPI, APIRouter, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dto.license import LicensesInfo

from api_wrapper import router


app = FastAPI()

api_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router(api_router.get, '/token')
async def get_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    pass


@router(api_router.get, '/users/me')
async def read_users_me(token: Annotated[str, Depends(oauth2_scheme)]):
    pass


@router(api_router.post, '/generate_license')
def generate_license(current_user: Annotated[str, Depends(oauth2_scheme)],
                     lic: LicensesInfo = Depends(LicensesInfo.as_form),
                     machine_digest_file: UploadFile = File(...)):
    pass

@router(api_router.get, '/all_licenses')
def get_all_licenses(current_user: Annotated[str, Depends(oauth2_scheme)]):
    pass


@router(api_router.get, "/license/{id}")
def find_license(id: int, current_user: Annotated[str, Depends(oauth2_scheme)]):
    pass

@router(api_router.get, "/machine_digest_file/{id}")
def find_machine_digest(id: int, current_user: Annotated[str, Depends(oauth2_scheme)]):
    pass

