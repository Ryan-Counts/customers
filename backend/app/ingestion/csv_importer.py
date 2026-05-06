import csv


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
    seen_emails = set()

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = (row.get("Name") or "").strip()
            email = (row.get("Email") or "").strip().lower()
            company = (row.get("Company") or "").strip()
            phone = (row.get("Phone") or "").strip()

            if not email or email in seen_emails:
                continue

            seen_emails.add(email)

            records.append({
                "name": name or email,
                "email": email,
                "company": company,
                "phone": phone,
                "source": "csv",
                "source_ref": filepath,
                "notes": "Imported from CSV",
            })

    return records