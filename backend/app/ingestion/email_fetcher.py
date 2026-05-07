# backend/app/ingestion/email_fetcher.py
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr, getaddresses
from flask import current_app


def _decode_str(value):
    """Decode an encoded email header value to a plain string."""
    if not value:
        return ""
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            safe_charset = charset or "utf-8"
            if safe_charset.lower() in ("unknown-8bit", "unknown", "x-unknown"):
                safe_charset = "utf-8"
            decoded.append(part.decode(safe_charset, errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded).strip()


def _get_body(msg):
    """Extract plain-text body from a (possibly multipart) message."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if ctype == "text/plain" and "attachment" not in disposition:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""

def parseCustomerInfo(body):
    data = {}

    for line in body.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        data[key] = value

    return {
        "name": data.get("name", ""),
        "email": data.get("email", "").lower(),
        "company": data.get("company", ""),
        "phone": data.get("phone #", ""),
        "course": data.get("course", ""),
    }

def _parse_contacts(msg):
    """
    Pull all sender/reply-to addresses out of a message.
    Returns a list of (name, email) tuples.
    """
    headers = []
    for header in ("From", "Reply-To"):
        raw = msg.get(header, "")
        if raw:
            headers.append(raw)
    contacts = getaddresses(headers)
    return [(name.strip(), addr.lower().strip()) for name, addr in contacts if addr]


def connect(host, port, user, password):
    """Open and authenticate an IMAP SSL connection."""
    mail = imaplib.IMAP4_SSL(host, port)
    mail.login(user, password)
    return mail


def fetch_emails(folder="INBOX", limit=1000, only_unseen=False):
    """
    Fetch emails from the configured IMAP account.

    Returns a list of dicts, one per unique sender address found,
    shaped to match the Customer model's fields.
    """
    cfg = current_app.config
    mail = connect(
        cfg["IMAP_HOST"],
        cfg["IMAP_PORT"],
        cfg["IMAP_USER"],
        cfg["IMAP_PASSWORD"],
    )
    print(f"Connected to IMAP server {cfg['IMAP_HOST']} as {cfg['IMAP_USER']}")
    try:
        mail.select(folder)

        search_criterion = "UNSEEN" if only_unseen else "ALL"
        _, data = mail.search(None, search_criterion)

        message_ids = data[0].split()
        if not message_ids:
            return []

        # Take the most recent `limit` messages
        message_ids = message_ids[-limit:]

        records = []
        seen_addresses = set()

        for uid in reversed(message_ids):   # newest first
            _, msg_data = mail.fetch(uid, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue

            raw = msg_data[0][1]
            if isinstance(raw, int):
                continue  # skip bad fetches):
            msg = email.message_from_bytes(raw)

            message_id = msg.get("Message-ID", "").strip()
            
            TARGET_SUBJECT = 'Walsh Agency "Sworn Declaration"'

            subject = _decode_str(msg.get("Subject", ""))
            if subject.strip() != TARGET_SUBJECT:
                continue

            body = _get_body(msg)
            parsed = parseCustomerInfo(body)

            if not parsed["email"]:
                continue  # skip bad/malformed emails

            addr = parsed["email"]

            if addr in seen_addresses:
                continue

            seen_addresses.add(addr)

            records.append({
                "name": parsed["name"] or addr,
                "email": addr,
                "company": parsed["company"],
                "phone": parsed["phone"],
                "course": parsed["course"],
                "date_taken": msg.get("Date"),
                "source": "email",
                "source_ref": message_id,
                "notes": f"Subject: {subject}",
            })
            
        return records

    finally:
        try:
            mail.logout()
        except Exception:
            pass
    