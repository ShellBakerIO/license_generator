from fastapi import Form
from pydantic import BaseModel

class LicensesInfo(BaseModel):
    company_name: str
    product_name: str
    license_users_count: int
    exp_time: str

    @classmethod
    def as_form(cls, company_name: str = Form(...), product_name: str = Form(...),
                license_users_count: int = Form(...), exp_time: str = Form(...)):

        return cls(company_name=company_name,
                   product_name=product_name,
                   license_users_count=license_users_count,
                   exp_time=exp_time)
