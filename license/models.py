from datetime import date

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, ARRAY
from sqlalchemy import create_engine
from config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

sqlite_database = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(sqlite_database, pool_pre_ping=True, echo=False)


class Base(DeclarativeBase):
    pass


class Licenses(Base):
    __tablename__ = "LicensesInfo"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    company_name = Column(String)
    product_name = Column(String)
    license_users_count = Column(Integer)
    exp_time = Column(DateTime, default=date(day=20, month=4, year=2152))
    additional_license_information = Column(String)
    machine_digest_file = Column(String)
    lic_file_name = Column(String)


class Software(Base):
    __tablename__ = "Software"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    company_name = Column(String, nullable=False)
    required_attributes = Column(ARRAY(String), nullable=True)
    license_generator_path = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)
