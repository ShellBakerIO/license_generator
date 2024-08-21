from pydantic import BaseModel
from typing import List


class AccessBase(BaseModel):
    name: str


class Access(AccessBase):
    id: int

    class Config:
        orm_mode = True


class RoleBase(BaseModel):
    name: str


class Role(RoleBase):
    id: int
    role_accesses: dict

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str


class User(UserBase):
    id: int
    roles: List[str]

    class Config:
        orm_mode = True
