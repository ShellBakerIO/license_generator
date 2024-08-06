from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import create_engine
from config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME


sqlite_database = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(sqlite_database, pool_pre_ping=True, echo=True)


class Base(DeclarativeBase):
    pass


class Licenses(Base):
    __tablename__ = "LicensesInfo"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    company_name = Column(String)
    product_name = Column(String)
    license_users_count = Column(Integer)
    exp_time = Column(DateTime)
    machine_digest_file = Column(String)
    lic_file_name = Column(String)


Base.metadata.create_all(bind=engine)
