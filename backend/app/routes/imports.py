# backend/app/routes/imports.py
from flask import Blueprint, jsonify
from sqlalchemy import Null
from ..ingestion.email_fetcher import fetch_emails
from ..ingestion.file_importer import import_from_files, parse_pdf_filename
from ..models import Customer
from ..models import CoursesTaken
from ..database import db
from dateutil import parser
from pathlib import Path
from flask import current_app
import pypdf
import re

def import_from_email():
    print("Starting email import...")
    records = fetch_emails(limit=1400, only_unseen=False)  # adjust as needed
    created, skipped = 0, 0
    engine = db.get_engine()
    session = db.Session(engine)

    #Loop over each record returned by the email fetch.
    for r in records:
        # If the record doesn't have an email, or if a customer with that email already exists, skip it.
        if not r["email"]:
            skipped += 1
            continue

        # If the record's email already exists in the database, skip it.
        #stmt = db.select(Customer).filter_by(email=r["email"])
        #exists = session.execute(stmt).first()
        exists = db.session.execute(db.select(Customer).filter_by(email=r["email"])).first()
        print(f"Processing email {r['email']}: exists in DB? {'Yes' if exists else 'No'}")
        if exists:
            skipped += 1
            continue

        # Using the session to add the new customer

        newCustomer = dict(name=r["name"].title() or Null, email=r["email"].lower(), phone=r.get("phone"), company=r.get("company"), source="email", source_ref=r.get("message_id"))
        db.session.add(Customer(**newCustomer))        

        created += 1
    print(f"Email import: {created} created, {skipped} skipped")
    db.session.commit()
    return jsonify({"created": created, "skipped": skipped})


def processCoursesTakenFromEmail():
    records = fetch_emails(limit=1400, only_unseen=False)  # adjust as needed
    created, skipped = 0, 0
    engine = db.get_engine()
    session = db.Session(engine)

    #Loop over each record returned by the email fetch.
    for r in records:
        # If the record doesn't have an email, or if a customer with that email already exists, skip it.
        if not r["email"]:
            skipped += 1
            continue
        
        # Get the customer's db id using their email.
        stmt = db.select(Customer).filter_by(email=r["email"])
        customer = session.execute(stmt).first()
        print(f"Processing course for email {r['email']}: found customer {customer[0].id if customer else 'None'}")
        if not customer:
            skipped += 1
            continue   
        customerID = customer[0].id

        # Get the course name from the email record. If it's missing, skip it.
        course_name = r.get("course")
        if not course_name:
            skipped += 1
            continue

        # Set the date taken based on the email record.
        date_taken = r.get("date_taken")
        date_object = parser.parse(date_taken) if date_taken else None

        if not date_object:
            skipped += 1
            continue

        # Create a new CoursesTaken record for this customer and course.
        courseTaken = dict(customer_id=customerID, course_name=course_name, date_taken=date_object, source="email")
        course_record = CoursesTaken(**courseTaken)
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

        foundCustomer = db.session.execute(db.select(Customer).filter_by(name=name)).first()
        
        customerID = foundCustomer.id if foundCustomer else None
        
        if not customerID:
            print(f"Customer '{name}' not found for file record. Skipping.")
            skipped += 1
            continue

        courseTaken = dict(customer_id=customerID, course_name=course, date_taken=date_taken, source="file")
        course_record = CoursesTaken(**courseTaken)
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
    # Implement CSV import logic here, similar to the email import.
    return jsonify({"message": "CSV import not implemented yet"})

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