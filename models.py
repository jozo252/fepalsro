from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    func,
    Boolean,
    ForeignKey,
    Float,
    Numeric,
    UniqueConstraint,
    JSON,
    Date,

)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped, mapped_column, backref
from datetime import datetime, date
from decimal import Decimal

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


DATABASE_URL = "sqlite:///./fepal.db"  # alebo tvoj názov

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # len pre SQLite
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False, 
)

Base = declarative_base()

class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password: str):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.hashed_password, password)
    
class Palet(Base):
    __tablename__="palets"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(100),nullable=False)
    sizes=Column(String(100),nullable=True)
def db_init():
    Base.metadata.create_all(bind=engine)
    print("Databaza ON")
#db_init()