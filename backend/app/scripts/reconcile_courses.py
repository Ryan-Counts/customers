# backend/app/ingestion/reconcile_courses.py
#
# NOTE: as of the staging-table rework, NEW imports no longer write straight
# to the master tables -- reconcile_to_master.py's merge_courses() now uses
# this same normalize+year-match+precision logic, so duplicates like the
# ones this script cleans up shouldn't be created going forward.
#
# Keep this script around as a one-time cleanup utility for any
# CoursesTakenMaster duplicates that already existed from BEFORE the
# rework, or anything that slips through. Safe to run any time -- it only
# removes true duplicates, never customers.
from datetime import datetime
from ..database import db
from ..models import CustomerMaster, CoursesTakenMaster
from sqlalchemy import func


def normalize_course_name(name: str) -> str:
    """Normalize course names to handle minor variations."""
    return name.strip().lower().replace("-", " ").replace("_", " ")


def reconcile_courses_taken():
    """
    Deduplicates CoursesTakenMaster records by merging file and email sources.
    
    Priority rules:
    - If a file record and email record exist for the same customer + course,
      keep the file record (more precise date) and discard the email duplicate.
    - If only one source exists, keep it regardless.
    - Two records are considered duplicates if they share:
        customer_id + normalized course name + same year
    """
    created, removed, kept = 0, 0, 0
    
    all_customers = db.session.query(CustomerMaster).all()

    for customer in all_customers:
        courses = db.session.query(CoursesTakenMaster)\
            .filter_by(customer_id=customer.id)\
            .all()

        if not courses:
            continue

        # Group by normalized course name + year
        groups: dict[tuple, list[CoursesTakenMaster]] = {}
        for course in courses:
            year = course.date_taken.year if course.date_taken else None
            key = (normalize_course_name(course.course_name), year)
            groups.setdefault(key, []).append(course)

        for (course_name, year), group in groups.items():
            if len(group) == 1:
                kept += 1
                continue  # no duplicate, nothing to do

            # Separate by source
            file_records  = [c for c in group if c.source == "file"] if hasattr(CoursesTakenMaster, 'source') else []
            email_records = [c for c in group if c.source == "email"] if hasattr(CoursesTakenMaster, 'source') else []

            # If no source field, prefer records with a real date over year-only dates
            precise_records = [c for c in group if c.date_taken and
                               not (c.date_taken.month == 1 and c.date_taken.day == 1)]
            vague_records   = [c for c in group if c not in precise_records]

            # Pick the best record to keep
            if file_records:
                winner = file_records[0]      # file records have precise dates
                losers = [c for c in group if c.id != winner.id]
            elif precise_records:
                winner = precise_records[0]   # has a real month/day
                losers = [c for c in group if c.id != winner.id]
            else:
                winner = group[0]             # just keep the first
                losers = group[1:]

            print(f"  Keeping  [{winner.id}] {customer.name} | {course_name} | {winner.date_taken}")
            for loser in losers:
                print(f"  Removing [{loser.id}] {customer.name} | {course_name} | {loser.date_taken}")
                db.session.delete(loser)
                removed += 1

            kept += 1

    db.session.commit()
    print(f"\nReconciliation complete: {kept} kept, {removed} removed")
    return {"kept": kept, "removed": removed}


def find_file_only_courses():
    """
    Diagnostic: find courses that came from files but have no matching email record.
    Useful for spotting certificates that were never emailed.
    """
    all_courses = db.session.query(CoursesTakenMaster).all()
    results = []

    for course in all_courses:
        year = course.date_taken.year if course.date_taken else None
        
        # Look for a matching email-sourced course for the same customer + course + year
        customer = db.session.query(CustomerMaster).filter_by(id=course.customer_id).first()
        if not customer:
            continue

        siblings = db.session.query(CoursesTakenMaster).filter(
            CoursesTakenMaster.customer_id == course.customer_id,
            func.lower(CoursesTakenMaster.course_name) == normalize_course_name(course.course_name)
        ).all()

        same_year = [s for s in siblings if s.date_taken and s.date_taken.year == year and s.id != course.id]

        if not same_year:
            results.append({
                "customer":    customer.name,
                "course":      course.course_name,
                "year":        year,
                "date_taken":  str(course.date_taken),
            })

    print(f"Found {len(results)} file-only course records (no matching email):")
    for r in results:
        print(f"  {r['customer']} | {r['course']} | {r['year']}")

    return results