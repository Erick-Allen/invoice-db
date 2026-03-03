from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

def to_cents(amount) -> int:
    """Coerce 12.34 / '12.34' -> 1234 (int cents)."""
    return int((Decimal(str(amount)) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def fmt_dollars(cents: int) -> str:
    """Convert integer cents (e.g. 35025) → formatted string '$350.25'."""
    return f"${(Decimal(cents) / Decimal(100)).quantize(Decimal('0.01'))}"

def fmt_optional(value: str | None, empty: str = "-"):
    return "-" if value is None else str(value)

def to_iso(date_str: str) -> str:
    """Coerce 'MM-DD-YYYY' / 'MM/DD/YYYY' / 'YYYY-MM-DD' → 'YYYY-MM-DD'."""
    if not date_str:
        return None
    
    formats = ("%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d")

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    raise ValueError(f"Invalid date format: {date_str} (expected MM-DD-YYYY or MM/DD/YYYY, or YYYY-MM-DD)")