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

            records.append({
                "name": name,
                "email": email,
                "company": company,
                "phone": phone,
                "source": "csv",
                "source_ref": filepath,
                "notes": "Imported from CSV"
            })

    return records
