import csv
from datetime import datetime
from ..models import CustomerCSV, CoursesTakenCSV
from ..database import db


def normalize_key(key):
    return key.strip().lower()


def get_value(row, *possible_keys):
    for key in row:
        norm = normalize_key(key)
        if norm in possible_keys:
            return row[key]
    return ""


def parse_csv(filepath):
    """
    Parse a CSV file of customers into normalized records.
    Returns a list of dicts shaped like your email ingestion output.
    """
    records = []

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            firstName = (row.get("FIRSTNAME") or "").strip().title()
            lastName  = (row.get("LASTNAME")  or "").strip().title()

            if firstName == "" or lastName == "":
                print(f"WARNING: Missing name in row: {row}")
                continue

            name = f"{firstName} {lastName}"
            email = (row.get("EMAIL") or "").strip().lower()
            company = (row.get("COMPANY") or "").strip()
            phone = (row.get("SMS") or "").strip()

            #course = (row.get("COURSE") or "").strip()

            if "Periodic" in (row.get("COURSE") or ""):
                course = "Periodic Ethics"
            elif "Initial" in (row.get("COURSE") or ""):
                course = "Initial Ethics"
            elif "Futures" in (row.get("COURSE") or ""):
                course = "AML For Futures Brokers"

            records.append({
                "name": name,
                "email": email,
                "company": company,
                "phone": phone,
                "course": course,
                "source_ref": filepath,
                "notes": "Imported from CSV",
            })

    return records


def save_csv_records(records):
    """
    Take parsed CSV records (from parse_csv) and write them into the
    CustomerCSV / CoursesTakenCSV staging tables. Does NOT touch the
    master tables -- that's reconcile_to_master.py's job.
    """
    created = 0
    for rec in records:
        customer = CustomerCSV(
            name=rec.get("name"), # type: ignore
            email=rec.get("email") or None, # type: ignore
            phone=rec.get("phone") or None, # type: ignore
            company=rec.get("company") or None, # type: ignore
            source_ref=rec.get("source_ref"), # type: ignore
            notes=rec.get("notes"), # type: ignore
        )
        db.session.add(customer)
        db.session.flush()  # get customer.id without a full commit

        course_name = rec.get("course")
        if course_name:
            db.session.add(CoursesTakenCSV(
                customer_id=customer.id, # type: ignore
                course_name=course_name, # type: ignore
                date_taken=None, # type: ignore
            ))

        created += 1

    db.session.commit()
    return created


def import_csv_file(filepath):
    """Convenience wrapper: parse a CSV and persist it to staging in one call."""
    records = parse_csv(filepath)
    return save_csv_records(records)