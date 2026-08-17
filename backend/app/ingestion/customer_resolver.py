from ..models import CustomerMaster, CustomerEmailAddress
from ..database import db


def normalize_name(name: str) -> str:
    return " ".join(p.strip().title() for p in name.split()) if name else ""


def find_customer_by_email(email: str) -> CustomerMaster | None:
    email_record = db.session.query(CustomerEmailAddress).filter_by(email=email.lower()).first()
    return email_record.customer if email_record else None


def find_customer_by_name(name: str) -> CustomerMaster | None:
    return db.session.query(CustomerMaster).filter(
        db.func.lower(CustomerMaster.name) == normalize_name(name).lower()
    ).first()


def add_email_to_customer(customer: CustomerMaster, email: str, source: str = "email", make_primary: bool = False) -> CustomerEmailAddress:
    """Add an email to a customer if it doesn't already exist."""
    existing = db.session.query(CustomerEmailAddress).filter_by(email=email.lower()).first()
    if existing:
        return existing  # already attached, nothing to do

    # If no emails yet, make this one primary regardless
    if not customer.emails:
        make_primary = True

    email_record = CustomerEmailAddress(
        customer_id=customer.id,
        email=email.lower(),
        is_primary=make_primary,
        source=source
    )
    db.session.add(email_record)
    return email_record


def resolve_or_create_customer(name: str, email: str | None, source: str = "email", **kwargs) -> tuple[CustomerMaster, bool]:
    """
    Find or create a MASTER customer using the following priority:
    1. Look up by email — if found, return that customer
    2. Look up by name  — if found, add the email to that customer
    3. Neither found    — create a new customer with this email

    Returns (customer, was_created).

    NOTE: with the staging-table rework, your ingestion routes (imports.py)
    no longer call this during import -- raw rows land in CustomerCSV /
    CustomerEmail / CustomerPDF staging instead, and reconcile_to_master.py
    handles dedup/merge into the master tables. This function is still here
    in case something else (manual customer creation in the admin UI, an
    API endpoint, etc.) calls it directly against the master tables. If
    nothing else calls it, it's safe to retire.
    """
    name = normalize_name(name)

    # 1. Check by email first
    if email:
        customer = find_customer_by_email(email)
        if customer:
            return customer, False

    # 2. Check by name
    customer = find_customer_by_name(name)
    if customer:
        if email:
            add_email_to_customer(customer, email, source=source)
            return customer, False

    # 3. Create new customer
    customer = CustomerMaster(name=name, source=source, **kwargs)
    db.session.add(customer)
    db.session.flush()  # get the ID before adding email

    if email:
        add_email_to_customer(customer, email, source=source, make_primary=True)
    return customer, True