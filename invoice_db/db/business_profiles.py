from dataclasses import dataclass
from sqlite3 import Row


@dataclass
class BusinessProfile:
    id: int
    workspace_id: int
    business_name: str | None
    email: str | None
    phone: str | None
    website: str | None
    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    default_payment_terms_days: int | None
    ways_to_pay: str | None
    default_tax_rate: str | None
    default_invoice_footer: str | None
    logo_url: str | None
    created_at: str
    updated_at: str


BUSINESS_PROFILE_FIELDS = (
    "business_name",
    "email",
    "phone",
    "website",
    "address_line1",
    "address_line2",
    "city",
    "state",
    "postal_code",
    "default_payment_terms_days",
    "ways_to_pay",
    "default_tax_rate",
    "default_invoice_footer",
    "logo_url",
)


def _to_business_profile(row: Row) -> BusinessProfile:
    return BusinessProfile(
        id=row["id"],
        workspace_id=row["workspace_id"],
        business_name=row["business_name"],
        email=row["email"],
        phone=row["phone"],
        website=row["website"],
        address_line1=row["address_line1"],
        address_line2=row["address_line2"],
        city=row["city"],
        state=row["state"],
        postal_code=row["postal_code"],
        default_payment_terms_days=row["default_payment_terms_days"],
        ways_to_pay=row["ways_to_pay"],
        default_tax_rate=row["default_tax_rate"],
        default_invoice_footer=row["default_invoice_footer"],
        logo_url=row["logo_url"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_business_profile(cursor, *, workspace_id: int) -> BusinessProfile | None:
    cursor.execute(
        """
        SELECT *
        FROM business_profiles
        WHERE workspace_id = ?
        """,
        (workspace_id,),
    )
    row = cursor.fetchone()
    return _to_business_profile(row) if row else None


def upsert_business_profile(
    cursor,
    *,
    workspace_id: int,
    profile_data: dict,
) -> BusinessProfile:
    values = [profile_data.get(field) for field in BUSINESS_PROFILE_FIELDS]

    cursor.execute(
        f"""
        INSERT INTO business_profiles (
            workspace_id,
            {", ".join(BUSINESS_PROFILE_FIELDS)}
        )
        VALUES (
            ?,
            {", ".join("?" for _ in BUSINESS_PROFILE_FIELDS)}
        )
        ON CONFLICT(workspace_id) DO UPDATE SET
            {", ".join(f"{field} = excluded.{field}" for field in BUSINESS_PROFILE_FIELDS)}
        """,
        (workspace_id, *values),
    )

    profile = get_business_profile(cursor, workspace_id=workspace_id)
    if profile is None:
        raise RuntimeError(f"Business profile was not saved for workspace {workspace_id}.")
    return profile
