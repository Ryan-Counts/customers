# backend/app/routes/imports.py
from flask import Blueprint, jsonify
from ..ingestion.customer_resolver import resolve_or_create_customer, find_customer_by_email
from ..ingestion.email_fetcher import fetch_emails
from ..ingestion.file_importer import import_from_files, parse_pdf_filename
from ..ingestion.csv_importer import parse_csv
from ..models import Customer, CoursesTaken, CustomerEmail
from ..database import db
from dateutil import parser
from pathlib import Path
from flask import current_app
from datetime import datetime

def import_from_email():
    print("Starting email import...")
    records = fetch_emails(limit=1400, only_unseen=False)  # adjust as needed
    created, skipped = 0, 0
    

    #Loop over each record returned by the email fetch.
    for r in records:
        # If the record doesn't have an email, or if a customer with that email already exists, skip it.
        if not r["email"]:
            skipped += 1
            continue
        

        customer, was_created = resolve_or_create_customer(
            name=r["name"],
            email=r["email"],
            source="email",
            phone=r.get("phone"),
            company=r.get("company"),
            source_ref=r.get("message_id")
        )

        if was_created:
            created += 1
        else:
            skipped += 1

    db.session.commit()
    print(f"Email import: {created} created, {skipped} skipped")
    return jsonify({"created": created, "skipped": skipped})

def import_from_csv(filepath):
    records = parse_csv(filepath)
    created, skipped = 0, 0

    for r in records:
        if not r.get("email") or not r.get("name"):
            skipped += 1
            continue

        customer, was_created = resolve_or_create_customer(
            name=r["name"],
            email=r["email"],
            source="csv",
            phone=r.get("phone"),
            company=r.get("company"),
            source_ref=filepath
        )

        if was_created:
            created += 1
        else:
            skipped += 1
        
    db.session.commit()
    print(f"CSV import: {created} created, {skipped} skipped")
    return {"created": created, "skipped": skipped}

def processCoursesTakenFromEmail():
    records = fetch_emails(limit=1400, only_unseen=False)  # adjust as needed
    created, skipped = 0, 0
    
    #Loop over each record returned by the email fetch.
    for r in records:
        # If the record doesn't have an email, or if a customer with that email already exists, skip it.
        if not r["email"]:
            skipped += 1
            continue
        
        # Get the customer's db id using their email.
        customer = find_customer_by_email(r["email"])
        if not customer:
            print(f"Customer with email {r['email']} not found. Skipping record.")
            skipped += 1
            continue   

        # Get the course name from the email record. If it's missing, skip it.
        course_name = r.get("course")
        if not course_name:
            skipped += 1
            continue

        # Set the date taken based on the email record.
        date_taken = r.get("date_taken")
        date_object = parser.parse(date_taken) if date_taken else None

        if not isinstance(date_object, datetime):
            skipped += 1
            continue

        # Create a new CoursesTaken record for this customer and course.
        course_record = CoursesTaken(
            customer_id=customer.id, 
            course_name=course_name, 
            date_taken=date_object, 
            source="email"
        )
        db.session.add(course_record)
        created += 1

    db.session.commit()
    return jsonify({"created": created, "skipped": skipped})


def processCoursesTakenFromFiles(file_records):
    created, skipped = 0, 0

    for r in file_records:
        name   = r.get("name")
        course = r.get("course")
        year   = r.get("year")
        date_taken = r.get("date_taken") or (f"{year}-01-01" if year else None)

        print(f"Processing file record: name='{name}', course='{course}', year='{year}', date_taken='{date_taken}'")

        if not name or not course:
            print(f"Skipping record due to missing name or course.")
            skipped += 1
            continue

        # Force proper spacing and casing on the name
        name = " ".join(part.capitalize() for part in name.split())

        if isinstance(date_taken, str):
            try:
                date_taken = datetime.strptime(date_taken, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date format for '{date_taken}'. Setting date_taken to default by year or None.")
                date_taken = datetime(int(year), 1, 1) if year else None

        # Look up by name, then fall back to email if availible.
        foundCustomer = db.session.query(Customer).filter(
            db.func.lower(Customer.name) == name.lower()
        ).first()

        print(f"Looking up customer by name '{name}': found {'Yes' if foundCustomer else 'No'}")
        
        
        if not foundCustomer and r.get("email"):
            foundCustomer = find_customer_by_email(r["email"])
            print(f"Looking up customer by email '{r.get('email')}': found {'Yes' if foundCustomer else 'No'}")
        
        if not foundCustomer:
            print(f"Customer '{name}' not found for file record. Skipping.")
            skipped += 1
            continue

        course_record = CoursesTaken(
            customer_id=foundCustomer.id, 
            course_name=course, 
            date_taken=date_taken, 
            source="file"
        )
        db.session.add(course_record)
        created += 1
        
    db.session.commit()
    print(f"File import - CoursesTaken: {created} created, {skipped} skipped")
    return jsonify({"created": created, "skipped": skipped})


imports_bp = Blueprint("imports_bp", __name__)

@imports_bp.route("/email", methods=["GET"])
def import_email():
    print("Starting email import...")
    emailImports = import_from_email()
    processCoursesTakenFromEmail()
    return emailImports

@imports_bp.route("/csv", methods=["POST"])
def import_csv():
    print("Starting CSV import...")
    cfg = current_app.config
    csvCustomers = import_from_csv(cfg["CSV_FILE_PATH"])
    return jsonify(csvCustomers)

@imports_bp.route("/db", methods=["POST"])
def import_db():
    # Implement database import logic here, similar to the email import.
    return jsonify({"message": "Database import not implemented yet"})

@imports_bp.route("/files", methods=["POST"])
def import_files():
    print("Starting file import...")
    filesImports = import_from_files()

    if isinstance(filesImports, tuple):  # Check if the result is a tuple (error case)
        return filesImports  # This will be the error response from import_from_files

    processCoursesTakenFromFiles(filesImports)
    return jsonify({"processed": len(filesImports)})