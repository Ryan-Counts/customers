# backend/app/models.py
from datetime import datetime
from .database import db
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey, String, Integer, DateTime, Boolean, Text, inspect
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column, relationship, InstanceState


# ════════════════════════════════════════════════════════════════════════════
# MASTER TABLES — the deduplicated, "real" customer record.
# These are what the reconcile script writes INTO.
# (Renamed from Customer/CustomerEmail/CoursesTaken to make the master/staging
#  split unambiguous. If you'd rather keep the old names, swap them back —
#  just make sure nothing else in the app still expects "Customer".)
# ════════════════════════════════════════════════════════════════════════════

class CustomerMaster(db.Model):
    __tablename__ = "customers_master"

    id         = mapped_column(Integer, primary_key=True)
    name       = mapped_column(String(200), unique=True, nullable=False)
    phone      = mapped_column(String(50))
    company    = mapped_column(String(200))
    status     = mapped_column(String(20), nullable=False, default="active")
    source     = mapped_column(String(50))       # which route FIRST created this master row
    source_ref = mapped_column(String(500))
    created_at = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    emails:          Mapped[List["CustomerEmailAddress"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    courses_taken:   Mapped[List["CoursesTakenMaster"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    contact_methods: Mapped[List["ContactMethod"]] = relationship(back_populates="customer", cascade="all, delete-orphan")

    def __init__(self, name: str, phone: Optional[str] = None, company: Optional[str] = None,
                 status: str = "active", source: Optional[str] = None, source_ref: Optional[str] = None):
        self.name       = name
        self.phone      = phone
        self.company    = company
        self.status     = status
        self.source     = source
        self.source_ref = source_ref

    def primary_email(self) -> str | None:
        primary = next((e for e in self.emails if e.is_primary), None)
        return primary.email if primary else None

    def to_dict(self, include_related=False):
        state: InstanceState = inspect(self) # type: ignore[assignment]
        d = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs} # type: ignore[union-attr]
        d["primary_email"] = self.primary_email()
        d["emails"]        = [e.email for e in self.emails]
        d["course_count"]  = len(self.courses_taken)
        if include_related:
            d["contact_methods"] = [cm.to_dict() for cm in self.contact_methods]
        return d


class CustomerEmailAddress(db.Model):
    """All known email addresses for a deduplicated master customer."""
    __tablename__ = "customer_email_addresses"

    id          = mapped_column(Integer, primary_key=True)
    customer_id = mapped_column(Integer, ForeignKey("customers_master.id"), nullable=False, index=True)
    email       = mapped_column(String(200), nullable=False)
    source      = mapped_column(String(50))   # which ingestion route first surfaced this address
    is_primary  = mapped_column(Boolean, nullable=False, default=False)
    created_at  = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    customer: Mapped[CustomerMaster] = relationship(back_populates="emails")

    def __init__(self, customer_id: int, email: str, is_primary: bool = False, source: str = "email"):
        self.customer_id = customer_id
        self.email       = email.lower()
        self.is_primary  = is_primary
        self.source      = source

    def to_dict(self):
        return dict(id=self.id, customer_id=self.customer_id, email=self.email,
                    is_primary=self.is_primary, created_at=self.created_at)


class CoursesTakenMaster(db.Model):
    """Deduplicated course history on the master customer."""
    __tablename__ = "courses_taken_master"

    id          = mapped_column(Integer, primary_key=True)
    customer_id = mapped_column(Integer, ForeignKey("customers_master.id"), nullable=False, index=True)
    course_name = mapped_column(String(200), nullable=False)
    date_taken  = mapped_column(DateTime)
    source      = mapped_column(String(50), default="unknown")  # which route this record came from

    customer: Mapped[CustomerMaster] = relationship(back_populates="courses_taken")

    def __init__(self, customer_id: int, course_name: str, date_taken: Optional[datetime] = None, source: str = "unknown"):
        self.customer_id = customer_id
        self.course_name = course_name
        self.date_taken  = date_taken
        self.source      = source

    def to_dict(self):
        return dict(id=self.id, customer_id=self.customer_id, course_name=self.course_name,
                    date_taken=self.date_taken.isoformat() if self.date_taken else None)


class ContactMethod(db.Model):
    __tablename__ = "contact_methods"

    id          = mapped_column(Integer, primary_key=True)
    customer_id = mapped_column(Integer, ForeignKey("customers_master.id"), nullable=False, index=True)
    type        = mapped_column(String(20), nullable=False)  # email|phone|address|url
    value       = mapped_column(Text, nullable=False)
    is_primary  = mapped_column(Boolean, nullable=False, default=False)

    customer: Mapped[CustomerMaster] = relationship(back_populates="contact_methods")

    def __init__(self, customer_id: int, type: str, value: str, is_primary: bool = False):
        self.customer_id = customer_id
        self.type        = type
        self.value       = value
        self.is_primary  = is_primary

    def to_dict(self):
        return dict(id=self.id, customer_id=self.customer_id, type=self.type, value=self.value, is_primary=self.is_primary)


# ════════════════════════════════════════════════════════════════════════════
# STAGING TABLES — one pair per ingestion route. Raw/unreconciled rows land
# here. Nothing here is deduplicated yet; the same real-world person can (and
# will) appear multiple times across these tables and even within one table.
# ════════════════════════════════════════════════════════════════════════════

class CustomerCSV(db.Model):
    __tablename__ = "customer_csv"

    id          = mapped_column(Integer, primary_key=True)
    name        = mapped_column(String(200), nullable=False)
    email       = mapped_column(String(200))
    phone       = mapped_column(String(50))
    company     = mapped_column(String(200))
    source_ref  = mapped_column(String(500))   # e.g. filepath of the CSV
    notes       = mapped_column(Text)
    imported_at = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    reconciled  = mapped_column(Boolean, nullable=False, default=False)   # set True once merged into master
    master_id   = mapped_column(Integer, ForeignKey("customers_master.id"), nullable=True)  # set once reconciled

    courses_taken: Mapped[List["CoursesTakenCSV"]] = relationship(back_populates="customer", cascade="all, delete-orphan")

    def to_dict(self):
        return dict(id=self.id, name=self.name, email=self.email, phone=self.phone,
                    company=self.company, source_ref=self.source_ref, notes=self.notes,
                    imported_at=self.imported_at, reconciled=self.reconciled, master_id=self.master_id)


class CoursesTakenCSV(db.Model):
    __tablename__ = "courses_taken_csv"

    id           = mapped_column(Integer, primary_key=True)
    customer_id  = mapped_column(Integer, ForeignKey("customer_csv.id"), nullable=False, index=True)
    course_name  = mapped_column(String(200), nullable=False)
    date_taken   = mapped_column(DateTime)

    customer: Mapped[CustomerCSV] = relationship(back_populates="courses_taken")

    def to_dict(self):
        return dict(id=self.id, customer_id=self.customer_id, course_name=self.course_name,
                    date_taken=self.date_taken.isoformat() if self.date_taken else None)


class CustomerEmail(db.Model):
    """Raw rows pulled from the IMAP/email ingestion route, pre-reconciliation."""
    __tablename__ = "customer_email"

    id           = mapped_column(Integer, primary_key=True)
    name         = mapped_column(String(200), nullable=False)
    email        = mapped_column(String(200))
    phone        = mapped_column(String(50))
    company      = mapped_column(String(200))
    source_ref   = mapped_column(String(500))   # Message-ID
    notes        = mapped_column(Text)
    imported_at  = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    reconciled   = mapped_column(Boolean, nullable=False, default=False)
    master_id    = mapped_column(Integer, ForeignKey("customers_master.id"), nullable=True)

    courses_taken: Mapped[List["CoursesTakenEmail"]] = relationship(back_populates="customer", cascade="all, delete-orphan")

    def to_dict(self):
        return dict(id=self.id, name=self.name, email=self.email, phone=self.phone,
                    company=self.company, source_ref=self.source_ref, notes=self.notes,
                    imported_at=self.imported_at, reconciled=self.reconciled, master_id=self.master_id)


class CoursesTakenEmail(db.Model):
    __tablename__ = "courses_taken_email"

    id           = mapped_column(Integer, primary_key=True)
    customer_id  = mapped_column(Integer, ForeignKey("customer_email.id"), nullable=False, index=True)
    course_name  = mapped_column(String(200), nullable=False)
    date_taken   = mapped_column(DateTime)

    customer: Mapped[CustomerEmail] = relationship(back_populates="courses_taken")

    def to_dict(self):
        return dict(id=self.id, customer_id=self.customer_id, course_name=self.course_name,
                    date_taken=self.date_taken.isoformat() if self.date_taken else None)


class CustomerPDF(db.Model):
    """Raw rows pulled from PDF-certificate ingestion, pre-reconciliation."""
    __tablename__ = "customer_pdf"

    id           = mapped_column(Integer, primary_key=True)
    name         = mapped_column(String(200))
    email        = mapped_column(String(200))
    phone        = mapped_column(String(50))
    company      = mapped_column(String(200))
    source_ref   = mapped_column(String(500))   # filename
    notes        = mapped_column(Text)
    imported_at  = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    reconciled   = mapped_column(Boolean, nullable=False, default=False)
    master_id    = mapped_column(Integer, ForeignKey("customers_master.id"), nullable=True)

    courses_taken: Mapped[List["CoursesTakenPDF"]] = relationship(back_populates="customer", cascade="all, delete-orphan")

    def to_dict(self):
        return dict(id=self.id, name=self.name, email=self.email, phone=self.phone,
                    company=self.company, source_ref=self.source_ref, notes=self.notes,
                    imported_at=self.imported_at, reconciled=self.reconciled, master_id=self.master_id)


class CoursesTakenPDF(db.Model):
    __tablename__ = "courses_taken_pdf"

    id           = mapped_column(Integer, primary_key=True)
    customer_id  = mapped_column(Integer, ForeignKey("customer_pdf.id"), nullable=False, index=True)
    course_name  = mapped_column(String(200), nullable=False)
    date_taken   = mapped_column(DateTime)

    customer: Mapped[CustomerPDF] = relationship(back_populates="courses_taken")

    def to_dict(self):
        return dict(id=self.id, customer_id=self.customer_id, course_name=self.course_name,
                    date_taken=self.date_taken.isoformat() if self.date_taken else None)