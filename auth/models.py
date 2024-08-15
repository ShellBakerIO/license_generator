from sqlalchemy import Column, Integer, String, ForeignKey, Table, JSON
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

sqlite_database = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(sqlite_database, pool_pre_ping=True, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


role_accesses = Table(
    'role_accesses', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('access_id', Integer, ForeignKey('accesses.id'))
)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String, ForeignKey('roles.name'), default=None)
    roles = relationship('Role', back_populates='users')


class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    role_accesses = Column(JSON, default={})
    accesses = relationship('Access', secondary='role_accesses', back_populates='roles')
    users = relationship('User', back_populates='roles')


class Access(Base):
    __tablename__ = 'accesses'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    roles = relationship('Role', secondary='role_accesses', back_populates='accesses')


Base.metadata.create_all(bind=engine)
