# backend/app/routes/imports.py
from flask import Blueprint, jsonify
from ..ingestion.email_fetcher import fetch_emails
from ..models import Customer
from ..models import CoursesTaken
from ..database import db
#from sqlalchemy.orm import Session

def import_from_email():
    records = fetch_emails(limit=1000, only_unseen=False)  # adjust as needed
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
        exists = db.select(Customer).filter_by(email=r["email"]).first()
        #exists = Customer.query.filter_by(email=r["email"]).first()
        if exists:
            skipped += 1
            continue

        # Using the session to add the new customer
        db.session.add(Customer(**r))        

        created += 1

    db.session.commit()
    return jsonify({"created": created, "skipped": skipped})


def processCoursesTakenFromEmail():
    records = fetch_emails(limit=1000, only_unseen=False)  # adjust as needed
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
        customer = db.select(Customer).filter_by(email=r["email"]).first()
        if not customer:
            skipped += 1
            continue   
        customer_id = customer.id

        # Get the course name from the email record. If it's missing, skip it.
        course_name = r.get("course")
        if not course_name:
            skipped += 1
            continue

        # Set the date taken based on the email record.
        date_taken = r.get("date_taken")
        if not date_taken:
            skipped += 1
            continue

        # Create a new CoursesTaken record for this customer and course.
        course_record = CoursesTaken(customer_id=customer_id, course_name=course_name, date_taken=date_taken)
        db.session.add(course_record)
        created += 1

    db.session.commit()
    return jsonify({"created": created, "skipped": skipped})

bp = Blueprint("imports", __name__)

@bp.route("/email", methods=["POST"])
def import_email():
    return import_from_email(), processCoursesTakenFromEmail()

@bp.route("/csv", methods=["POST"])
def import_csv():
    # Implement CSV import logic here, similar to the email import.
    return jsonify({"message": "CSV import not implemented yet"})

@bp.route("/db", methods=["POST"])
def import_db():
    # Implement database import logic here, similar to the email import.
    return jsonify({"message": "Database import not implemented yet"})