from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy import Column, Integer, String, Table, ForeignKey, DateTime
from sqlalchemy import create_engine
from config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME


sqlite_database = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(sqlite_database, pool_pre_ping=True, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


user_roles = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

role_accesses = Table(
    'role_accesses', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('access_id', Integer, ForeignKey('accesses.id'))
)


class Licenses(Base):
    __tablename__ = "LicensesInfo"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    company_name = Column(String)
    product_name = Column(String)
    license_users_count = Column(Integer)
    exp_time = Column(DateTime)
    machine_digest_file = Column(String)
    lic_file_name = Column(String)


class UserAuth(Base):
    __tablename__ = "User"

    id = Column(Integer, autoincrement=True, nullable=False)
    username = Column(String, primary_key=True)
    token = Column(String)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    roles = relationship('Role', secondary=user_roles, back_populates='users')


class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    accesses = relationship('Access', secondary=role_accesses, back_populates='roles')
    users = relationship('User', secondary=user_roles, back_populates='roles')


class Access(Base):
    __tablename__ = 'accesses'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    roles = relationship('Role', secondary=role_accesses, back_populates='accesses')


Base.metadata.create_all(bind=engine)
