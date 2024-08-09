from pydantic import BaseModel
from typing import List, Optional


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
    accesses: List[Access] = []

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    role_id: int


class User(UserBase):
    id: int

    class Config:
        orm_mode = True
