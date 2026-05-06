# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///customers.db")

    # Email
    IMAP_HOST     = os.getenv("IMAP_HOST", "mail.yourdomain.com")
    IMAP_PORT     = int(os.getenv("IMAP_PORT", 993))
    IMAP_USER     = os.getenv("IMAP_USER")      # full email address
    IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")