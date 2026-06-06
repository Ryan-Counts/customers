import re
from pathlib import Path
from flask import current_app, jsonify
import pypdf
from datetime import datetime
from ..database import db

# ── Course Aliases ─────────────────────────────────────────────────────────────
COURSE_ALIASES = [
    (r"periodic_ethics",  "Periodic Ethics"),
    (r"initial_ethics",   "Initial Ethics"),
    (r"aml_rmlo",         "AML RMLO"),
    (r"aml_msb",          "AML MSB"),
    (r"aml_futures",      "AML Futures"),
    # Legacy (no separators)
    (r"periodicethics",   "Periodic Ethics"),
    (r"initialethics",    "Initial Ethics"),
    (r"amlfutures",       "AML Futures"),
    (r"amlrmlo",          "AML RMLO"),
    (r"amlmsb",           "AML MSB"),
    # Mortgage aliases → AML RMLO
    (r"aml_mortgage",     "AML RMLO"),   # modern: aml_mortgage-_first_last_year
    (r"amlmortgage",      "AML RMLO"),   # legacy: FirstLastAMLMortgageYear
    (r"mortgage",         "AML RMLO"),   # bare fallback: FirstLastMortgageYear
]

YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

# ── Modern: periodic_ethics-_first_last_2026 ───────────────────────────────────
MODERN_RE = re.compile(
    r"^(?P<course>[a-z]+(?:_[a-z]+)*)"  # course: lowercase words joined by underscores
    r"-_"                                # literal separator between course and name
    r"(?P<first>[a-z]+)"                # first name
    r"_(?P<last>[a-z]+)"                # last name
    r"_(?P<year>(19|20)\d{2})$",        # year at end
    re.IGNORECASE
)

# ── Legacy: FirstLastPeriodicEthics2021 ────────────────────────────────────────
LEGACY_RE = re.compile(
    r"^(?P<first>[A-Z][a-z]+)"          # Firstname
    r"(?P<last>[A-Z][a-z]+)"            # Lastname
    r"(?P<course>[A-Za-z]+?)"           # Course (non-greedy, no separators)
    r"(?P<year>(19|20)\d{2})$"          # Year at end
)

# Handles formats like "December 1st, 2023" / "January 15th, 2022" etc.
DATE_RE = re.compile(
    r"\b(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?"  # optional ordinal suffix
    r",?\s+(?P<year>(19|20)\d{2})\b",
    re.IGNORECASE
)

def extract_name_from_text(text: str) -> str | None:
    NAME_RE = re.compile(r"presented to:\s*(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", re.IGNORECASE)
    m = NAME_RE.search(text)
    return m.group("name").strip() if m else None


def process_pdf(filepath: str | Path) -> dict:
    path = Path(filepath)

    # Parse what we can from filename
    parsed = parse_pdf_filename(path)

    # Try to extract richer data from the text itself
    try:
        text = _extract_text(path)

        name_from_text = extract_name_from_text(text)
        date_from_text = extract_date(text)

        # Prefer text-extracted values over filename-parsed ones
        if name_from_text:
            parsed["name"] = name_from_text
        if date_from_text:
            parsed["date_taken"] = date_from_text

    except Exception as e:
        print(f"WARNING: Could not extract text from {path.name}: {e}")
        parsed["date_taken"] = None

    return parsed

def import_from_files():
    cfg = current_app.config
    directory = cfg.get("FILES_DIRECTORY", "files_to_import")

    if not Path(directory).exists():
        print(f"ERROR: Directory '{directory}' does not exist.")
        return jsonify({"error": f"Directory '{directory}' does not exist."}), 400
    created, skipped = 0, 0
    results = []

    pdf_files = list(Path(directory).glob("**/*.pdf"))  # ** means search subdirectories too

    print(f"Found {len(pdf_files)} PDF(s) in {directory}")

    for pdf_path in pdf_files:
        try:
            result = process_pdf(pdf_path)
            results.append(result)
            print(f"Processed: {pdf_path.name} -> {result}")
        except Exception as e:
            print(f"Failed to process {pdf_path.name}: {e}")
            continue
    
    return results

def _extract_text(pdf_path: Path) -> str:
    text_parts = []
    with open(pdf_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)

def extract_date(text: str) -> str | None:
    """Extract and normalize a date from certificate text."""
    m = DATE_RE.search(text)
    if not m:
        return None
    try:
        raw = f"{m.group('month')} {m.group('day')} {m.group('year')}"
        dt = datetime.strptime(raw, "%B %d %Y")
        return dt.strftime("%Y-%m-%d")  # normalize to ISO format
    except ValueError:
        return None

def normalize_course(raw: str) -> str:
    raw_lower = raw.lower()
    for pattern, name in COURSE_ALIASES:
        if re.search(pattern, raw_lower):
            return name
    return raw.replace("_", " ").strip().title()


def parse_pdf_filename(filepath: str | Path) -> dict:
    path = Path(filepath)
    stem = path.stem  # e.g. "periodic_ethics-_john_smith_2026"

    # ── Modern ────────────────────────────────────────────────────────────────
    m = MODERN_RE.match(stem)
    if m:
        return {
            "filename": path.name,
            "format":   "modern",
            "name":     f"{m.group('first').title()} {m.group('last').title()}",
            "course":   normalize_course(m.group("course")),
            "year":     m.group("year"),
        }

    # ── Legacy ────────────────────────────────────────────────────────────────
    m = LEGACY_RE.match(stem)
    if m:
        return {
            "filename": path.name,
            "format":   "legacy",
            "name":     f"{m.group('first')} {m.group('last')}",
            "course":   normalize_course(m.group("course")),
            "year":     m.group("year"),
        }

    # ── Unrecognized ──────────────────────────────────────────────────────────
    year_match = YEAR_RE.search(stem)
    course = next(
        (name for pattern, name in COURSE_ALIASES
         if re.search(pattern, stem.lower())),
        "Unknown"
    )
    print(f"WARNING: Could not parse filename: {path.name}")
    return {
        "filename": path.name,
        "format":   "unknown",
        "name":     None,
        "course":   course,
        "year":     year_match.group() if year_match else None,
    }


