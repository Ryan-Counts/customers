# backend/app/models.py
from datetime import datetime
from .database import db
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey, String, Integer, DateTime, Boolean, Text, inspect
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Customer(db.Model):
    __tablename__ = "customers"

    id         = mapped_column(Integer, primary_key=True)
    name       = mapped_column(String(200), unique=True, nullable=False)
    #email      = mapped_column(String(200), index=True)
    phone      = mapped_column(String(50))
    company    = mapped_column(String(200))
    status     = mapped_column(String(20), nullable=False, default="active")
    source     = mapped_column(String(50))
    source_ref = mapped_column(String(500))
    created_at = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    emails:          Mapped[List["CustomerEmail"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    courses_taken:   Mapped[List["CoursesTaken"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    contact_methods: Mapped[List["ContactMethod"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
   
    def __init__(self, name: str, phone: Optional[str] = None, company: Optional[str] = None, status: str = "active", source: Optional[str] = None, source_ref: Optional[str] = None):
        self.name       = name
        #self.email      = email.lower() if email else None
        self.phone      = phone
        self.company    = company
        self.status     = status
        self.source     = source
        self.source_ref = source_ref

    def primary_email(self) -> str | None:
        primary = next((e for e in self.emails if e.is_primary), None)
        return primary.email if primary else None
    
    def to_dict(self, include_related=False):
        d = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        d["primary_email"] = self.primary_email()
        d["emails"]        = [e.email for e in self.emails]
        d["course_count"]  = len(self.courses_taken)  # <-- add this
        if include_related:
            d["contact_methods"] = [cm.to_dict() for cm in self.contact_methods]
        return d

class CustomerEmail(db.Model):
    __tablename__ = "customer_emails"

    id          = mapped_column(Integer, primary_key=True)
    customer_id = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    email       = mapped_column(String(200), nullable=False)
    source      = mapped_column(String(50)) # e.g. "email", "file", "csv"
    is_primary  = mapped_column(Boolean, nullable=False, default=False)
    created_at  = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    customer: Mapped[Customer] = relationship(back_populates="emails")

    def __init__(self, customer_id: int, email: str, is_primary: bool = False, source: str = "email"):
        self.customer_id = customer_id
        self.email       = email.lower()
        self.is_primary  = is_primary
        self.source      = source

    def to_dict(self):
        return dict(id=self.id, customer_id=self.customer_id, email=self.email, is_primary=self.is_primary, created_at=self.created_at)

class CoursesTaken(db.Model):
    __tablename__ = "courses_taken"

    id           = mapped_column(Integer, primary_key=True)
    customer_id  = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    course_name  = mapped_column(String(200), nullable=False)
    date_taken   = mapped_column(DateTime)
    source       = mapped_column(String(50), default="unknown")

    customer: Mapped[Customer] = relationship(back_populates="courses_taken")

    def __init__(self, customer_id: int, course_name: str, date_taken: Optional[datetime] = None, source: str = "unknown"):
        self.customer_id = customer_id
        self.course_name = course_name
        self.date_taken  = date_taken
        self.source      = source

    def to_dict(self):
        return dict(id=self.id, customer_id=self.customer_id, course_name=self.course_name, date_taken=self.date_taken.isoformat() if self.date_taken else None)
    

class ContactMethod(db.Model):
    __tablename__ = "contact_methods"

    id          = mapped_column(Integer, primary_key=True)
    customer_id = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    type        = mapped_column(String(20), nullable=False)  # email|phone|address|url
    value       = mapped_column(Text, nullable=False)
    is_primary  = mapped_column(Boolean, nullable=False, default=False)

    customer: Mapped[Customer] = relationship(back_populates="contact_methods")

    def __init__(self, customer_id: int, type: str, value: str, is_primary: bool = False):
        self.customer_id = customer_id
        self.type        = type
        self.value       = value
        self.is_primary  = is_primary

    def to_dict(self):
        return dict(id=self.id, customer_id=self.customer_id, type=self.type, value=self.value, is_primary=self.is_primary)
