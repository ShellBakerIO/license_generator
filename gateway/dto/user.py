from pydantic import BaseModel
from typing import List


class Role_to_User(BaseModel):
    user_id: int
    role_id: int
    added: bool


class Access_to_Role(BaseModel):
    role_id: int
    access_id: int
    has_access: bool


class AccessBase(BaseModel):
    name: str


class AccessCreate(AccessBase):
    pass


class Access(AccessBase):
    id: int

    class Config:
        orm_mode = True


class RoleBase(BaseModel):
    name: str


class RoleCreate(RoleBase):
    pass


class RoleDelete(BaseModel):
    id: int


class Role(RoleBase):
    id: int
    role_accesses: dict

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    pass


class UserDelete(BaseModel):
    id: int


class User(UserBase):
    id: int
    roles: List[str]

    class Config:
        orm_mode = True
