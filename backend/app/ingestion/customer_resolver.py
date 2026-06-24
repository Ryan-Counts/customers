from ..models import Customer, CustomerEmail
from ..database import db


def normalize_name(name: str) -> str:
    return " ".join(p.strip().title() for p in name.split()) if name else ""


def find_customer_by_email(email: str) -> Customer | None:
    email_record = db.session.query(CustomerEmail).filter_by(email=email.lower()).first()
    return email_record.customer if email_record else None


def find_customer_by_name(name: str) -> Customer | None:
    return db.session.query(Customer).filter(
        db.func.lower(Customer.name) == normalize_name(name).lower()
    ).first()


def add_email_to_customer(customer: Customer, email: str, source: str = "email", make_primary: bool = False) -> CustomerEmail:
    """Add an email to a customer if it doesn't already exist."""
    existing = db.session.query(CustomerEmail).filter_by(email=email.lower()).first()
    if existing:
        return existing  # already attached, nothing to do

    # If no emails yet, make this one primary regardless
    if not customer.emails:
        make_primary = True

    email_record = CustomerEmail(
        customer_id=customer.id,
        email=email.lower(),
        is_primary=make_primary,
        source=source
    )
    db.session.add(email_record)
    return email_record


def resolve_or_create_customer(name: str, email: str | None, source: str = "email", **kwargs) -> tuple[Customer, bool]:
    """
    Find or create a customer using the following priority:
    1. Look up by email — if found, return that customer
    2. Look up by name  — if found, add the email to that customer
    3. Neither found    — create a new customer with this email

    Returns (customer, was_created).
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
    customer = Customer(name=name, source=source, **kwargs)
    db.session.add(customer)
    db.session.flush()  # get the ID before adding email

    if email:
        add_email_to_customer(customer, email, source=source, make_primary=True)
    return customer, True