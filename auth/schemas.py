from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union


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
    email: EmailStr
    password: str


class User(UserBase):
    id: int
    roles: List[str]

    class Config:
        from_attributes = True


class UserLDAP(UserBase):
    login: str
    email: Optional[EmailStr]


class UserCreate(UserBase):
    pass


class AccessEntries(BaseModel):
    is_auth: bool
    accesses: List[str]
    role: Optional[Union[str, List[str], List[Role]]]
