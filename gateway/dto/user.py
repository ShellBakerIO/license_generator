from pydantic import BaseModel


class LoginForm(BaseModel):
    username: str
    password: str


class RoleBase(BaseModel):
    name: str


class RoleCreate(RoleBase):
    pass


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    pass


class AccessBase(BaseModel):
    name: str


class AccessCreate(AccessBase):
    pass
