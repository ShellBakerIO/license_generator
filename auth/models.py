from sqlalchemy import Column, Integer, String, JSON, ARRAY
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

sqlite_database = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(sqlite_database, pool_pre_ping=True, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    roles = Column(ARRAY(String), default=[])


class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    role_accesses = Column(JSON, default={})


class Access(Base):
    __tablename__ = 'accesses'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)


Base.metadata.create_all(bind=engine)
