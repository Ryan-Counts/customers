# backend/app/routes/imports.py
from flask import Blueprint, jsonify, current_app

from ..ingestion.email_fetcher import fetch_emails, save_email_records
from ..ingestion.file_importer import import_from_files
from ..ingestion.csv_importer import parse_csv, save_csv_records
from ..ingestion.reconcile_to_master import run_reconciliation
from ..database import db


def import_from_email():
    """Pull from IMAP and land everything in the CustomerEmail staging table."""
    print("Starting email import...")
    records = fetch_emails(limit=1400, only_unseen=False)  # adjust as needed
    created = save_email_records(records)
    skipped = len(records) - created
    print(f"Email import (staging): {created} staged, {skipped} skipped")
    return jsonify({"staged": created, "skipped": skipped})


def import_from_csv(filepath):
    """Parse a CSV file and land everything in the CustomerCSV staging table."""
    records = parse_csv(filepath)
    created = save_csv_records(records)
    skipped = len(records) - created
    print(f"CSV import (staging): {created} staged, {skipped} skipped")
    return {"staged": created, "skipped": skipped}


imports_bp = Blueprint("imports_bp", __name__)


@imports_bp.route("/email", methods=["GET"])
def import_email():
    print("Starting email import...")
    return import_from_email()


@imports_bp.route("/csv", methods=["POST"])
def import_csv():
    print("Starting CSV import...")
    cfg = current_app.config
    csvCustomers = import_from_csv(cfg["CSV_FILE_PATH"])
    return jsonify(csvCustomers)


@imports_bp.route("/files", methods=["POST"])
def import_files():
    """import_from_files() now stages each PDF into CustomerPDF/CoursesTakenPDF itself."""
    print("Starting file import...")
    filesImports = import_from_files()

    if isinstance(filesImports, tuple):  # Check if the result is a tuple (error case)
        return filesImports  # This will be the error response from import_from_files

    return jsonify({"staged": len(filesImports)})


@imports_bp.route("/reconcile", methods=["POST"])
def reconcile():
    """
    Merge everything sitting in the staging tables (CustomerCSV/Email/PDF)
    into the deduplicated master tables. Safe to call repeatedly --
    already-reconciled rows are skipped.
    """
    print("Starting reconciliation...")
    summary = run_reconciliation()
    return jsonify(summary)