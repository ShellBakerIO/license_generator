from pydantic import BaseModel
from typing import List


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


class Role(RoleBase):
    id: int
    role_accesses: dict

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    roles: List[str]

    class Config:
        orm_mode = True
