# backend/app/models.py
from datetime import datetime
from .database import db
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import Boolean
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    id         = mapped_column(Integer, primary_key=True)
    name       = mapped_column(String(200), nullable=False)
    email      = mapped_column(String(200), unique=True, index=True)
    phone      = mapped_column(String(50))
    company    = mapped_column(String(200), index=True)
    status     = mapped_column(String(20), nullable=False, default="active")
    source     = mapped_column(String(50))
    source_ref = mapped_column(String(500))
    created_at = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    courses_taken:  Mapped[List["CoursesTaken"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    contact_methods: Mapped[List["ContactMethod"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
   
    def to_dict(self, include_related=False):
        d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if include_related:
            d["contact_methods"] = [cm.to_dict() for cm in self.contact_methods]
        return d

class CoursesTaken(Base):
    __tablename__ = "courses_taken"

    id           = mapped_column(Integer, primary_key=True)
    customer_id  = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    course_name  = mapped_column(String(200), nullable=False)
    date_taken   = mapped_column(DateTime)

    customer: Mapped[Customer] = relationship(back_populates="courses_taken")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ContactMethod(Base):
    __tablename__ = "contact_methods"

    id          = mapped_column(Integer, primary_key=True)
    customer_id = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    type        = mapped_column(String(20), nullable=False)  # email|phone|address|url
    value       = mapped_column(Text, nullable=False)
    is_primary  = mapped_column(Boolean, nullable=False, default=False)

    customer: Mapped[Customer] = relationship(back_populates="contact_methods")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
