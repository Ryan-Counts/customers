# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class config:
    # SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///customers.db")

    # Email
    IMAP_HOST     = os.getenv("IMAP_HOST")
    IMAP_PORT     = int(os.getenv("IMAP_PORT", 993))
    IMAP_USER     = os.getenv("IMAP_USER")      # full email address
    IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")

    # File import
    FILES_DIRECTORY = os.getenv("FILES_DIRECTORY", "files_to_import")

    # CSV import
    CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", "customers.csv")