from datetime import date

from fastapi import Form
from pydantic import BaseModel
from typing import Optional, List


class LicensesInfo(BaseModel):
    company_name: str
    product_name: str
    license_users_count: int
    exp_time: str
    additional_license_information: str

    @classmethod
    def as_form(
            cls,
            company_name: str = Form(...),
            product_name: str = Form(...),
            license_users_count: int = Form(...),
            exp_time: str = Form(str(date(day=20, month=4, year=2152))),
            additional_license_information: str = Form(...),
    ):
        return cls(
            company_name=company_name,
            product_name=product_name,
            license_users_count=license_users_count,
            exp_time=exp_time,
            additional_license_information=additional_license_information,
        )


class SoftwareBase(BaseModel):
    company_name: Optional[str] = None
    required_attributes: Optional[List] = None
    license_generator_path: Optional[str] = None


class SoftwareCreate(SoftwareBase):
    company_name: str


class SoftwareUpdate(SoftwareBase):
    pass


class SoftwareResponse(SoftwareBase):
    id: int

    class Config:
        from_attributes = True
