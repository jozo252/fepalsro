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
    palets = relationship("Palet", back_populates="user", cascade="all, delete-orphan")
    stocks = relationship("Stock", back_populates="user", cascade="all, delete-orphan")
    stock_moves = relationship("StockMove", back_populates="user", cascade="all, delete-orphan")
    shipments = relationship("Shipment", back_populates="user", cascade="all, delete-orphan")


    def set_password(self, password: str):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.hashed_password, password)
    
    
class Palet(Base):
    __tablename__="palets"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(100),nullable=False)
    sizes=Column(String(100),nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="palets")
    stock = relationship("Stock", back_populates="palet", uselist=False, cascade="all, delete-orphan")
    stock_moves = relationship("StockMove", back_populates="palet", cascade="all, delete-orphan")
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_palet_user_name"),
    )

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    palet_id = Column(Integer, ForeignKey("palets.id"), nullable=False, index=True)

    qty = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "palet_id", name="uq_stock_user_palet"),
    )

    user = relationship("User", back_populates="stocks")
    palet = relationship("Palet", back_populates="stock")

class StockMove(Base):
    __tablename__ = "stock_moves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    palet_id = Column(Integer, ForeignKey("palets.id"), nullable=False, index=True)

    delta = Column(Integer, nullable=False)   # +príjem / -výdaj
    note = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="stock_moves")
    palet = relationship("Palet", back_populates="stock_moves")
    shipment_id=Column(Integer, ForeignKey("shipments.id"), nullable=True,index=True)
    shipment= relationship("Shipment",back_populates="stock_moves")

class Shipment(Base):
    __tablename__="shipments"
    id=Column(Integer,primary_key=True,index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name=Column(String(100),nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    moves=relationship("StockMove", back_populates="shipment", cascade="all, delete-orphan")
    user=relationship("User", back_populates="shipments")




def db_init():
    Base.metadata.create_all(bind=engine)
    print("Databaza ON")
#db_init()