"""
reconcile_to_master.py

Walks every staging table (CustomerCSV, CustomerEmail, CustomerPDF -- plus
their CoursesTaken* tables) and merges them into the deduplicated master
tables (CustomerMaster, CustomerEmailAddress, CoursesTakenMaster).

Identity rule (in priority order):
  1. Match on email address (case-insensitive) against CustomerEmailAddress.
  2. Fall back to matching on normalized name against CustomerMaster.name.
  3. Otherwise, create a brand-new CustomerMaster row.

A staging row is marked `reconciled=True` and stamped with `master_id`
once it's been merged, so reruns are idempotent -- already-reconciled rows
are skipped on subsequent runs.

Course dedup rule: a course is only inserted into CoursesTakenMaster if
that exact (customer, course_name) pair doesn't already exist there. If it
already exists, the staging course is skipped (not inserted again), even
if the date_taken differs slightly across sources.

Run with:  python -m backend.app.scripts.reconcile_to_master
(adjust the import path below to match wherever you place this file)
"""

from datetime import datetime

from ..database import db
from ..models import (
    CustomerMaster, CustomerEmailAddress, CoursesTakenMaster,
    CustomerCSV, CoursesTakenCSV,
    CustomerEmail, CoursesTakenEmail,
    CustomerPDF, CoursesTakenPDF,
)


def _normalize_name(name):
    return (name or "").strip().lower()


def _normalize_email(email):
    return (email or "").strip().lower()


def find_or_create_master(name, email, phone, company, source, source_ref):
    """
    Look up an existing master customer by email first, then by name.
    Create one if neither matches.
    """
    master = None
    norm_email = _normalize_email(email)

    if norm_email:
        existing_email = (
            db.session.query(CustomerEmailAddress)
            .filter(CustomerEmailAddress.email == norm_email) # type: ignore
            .first()
        )
        if existing_email:
            master = existing_email.customer

    if master is None:
        norm_name = _normalize_name(name)
        if norm_name != "":
            master = (
                db.session.query(CustomerMaster)
                .filter(db.func.lower(CustomerMaster.name) == norm_name)
                .first()
            )

    if master is None:
        master = CustomerMaster(
            name=name,
            phone=phone,
            company=company,
            source=source,
            source_ref=source_ref,
        )
        db.session.add(master)
        db.session.flush()  # need master.id below

    # Backfill any blank fields on the master from this row, without
    # clobbering data that's already there.
    if not master.phone and phone:
        master.phone = phone
    if not master.company and company:
        master.company = company

    # Attach the email if it's new for this master.
    if norm_email:
        already_has = any(e.email == norm_email for e in master.emails)
        if not already_has:
            is_primary = len(master.emails) == 0
            db.session.add(CustomerEmailAddress(
                customer_id=master.id,
                email=norm_email,
                is_primary=is_primary,
                source=source,
            ))

    return master


def normalize_course_name(name):
    """Normalize course names to handle minor variations (matches reconcile_courses.py)."""
    return name.strip().lower().replace("-", " ").replace("_", " ") if name else ""


def _is_precise(date_taken):
    """True if a date looks like a real calendar date rather than a Jan-1 placeholder."""
    return bool(date_taken) and not (date_taken.month == 1 and date_taken.day == 1)


def merge_courses(master, staged_courses, source):
    """
    Insert each staged course into CoursesTakenMaster unless an equivalent
    one already exists. Two courses are considered the same if they share
    a normalized course name + year (mirrors reconcile_courses.py's rules).

    If a staged course duplicates an existing master course but has a more
    precise date (real month/day vs. a Jan-1 placeholder), upgrade the
    master row's date_taken instead of skipping -- this preferences a
    precise file-derived date over a vague CSV/email-derived one regardless
    of which arrived first.
    """
    # key -> existing CoursesTakenMaster row
    existing_by_key = {}
    for c in master.courses_taken:
        year = c.date_taken.year if c.date_taken else None
        existing_by_key[(normalize_course_name(c.course_name), year)] = c

    inserted = 0
    for course in staged_courses:
        year = course.date_taken.year if course.date_taken else None
        key = (normalize_course_name(course.course_name), year)

        existing = existing_by_key.get(key)
        if existing is None:
            new_row = CoursesTakenMaster(
                customer_id=master.id,
                course_name=course.course_name,
                date_taken=course.date_taken,
                source=source,
            )
            db.session.add(new_row)
            existing_by_key[key] = new_row
            inserted += 1
            continue

        # Duplicate -- upgrade the date if the staged copy is more precise.
        if _is_precise(course.date_taken) and not _is_precise(existing.date_taken):
            existing.date_taken = course.date_taken
            existing.source = source

    return inserted


def reconcile_table(staging_model, courses_model, source_label):
    """
    Generic reconciliation pass over one staging table.
    Returns (rows_processed, masters_touched, courses_inserted).
    """
    rows = (
        db.session.query(staging_model)
        .filter(staging_model.reconciled == False)  # noqa: E712
        .all()
    )

    rows_processed = 0
    courses_inserted = 0

    for row in rows:
        if(row.name or row.email):
            master = find_or_create_master(
                name=row.name,
                email=row.email,
                phone=row.phone,
                company=row.company,
                source=source_label,
                source_ref=row.source_ref,
            )

        courses_inserted += merge_courses(master, row.courses_taken, source_label)

        row.reconciled = True
        row.master_id = master.id
        rows_processed += 1

    db.session.commit()
    return rows_processed


def run_reconciliation():
    summary = {}

    summary["csv"] = reconcile_table(CustomerCSV, CoursesTakenCSV, "csv")
    summary["email"] = reconcile_table(CustomerEmail, CoursesTakenEmail, "email")
    summary["pdf"] = reconcile_table(CustomerPDF, CoursesTakenPDF, "pdf")

    total = sum(summary.values())
    print(f"Reconciliation complete. Rows merged -> csv: {summary['csv']}, "
          f"email: {summary['email']}, pdf: {summary['pdf']} (total {total})")
    return summary


if __name__ == "__main__":
    # Adjust this to however your app builds its Flask app + app context,
    # e.g.:
    #
    # from .app_factory import create_app
    # app = create_app()
    # with app.app_context():
    #     run_reconciliation()
    run_reconciliation()