from invoice_db.db import business_profiles as business_profiles_db
from invoice_db.db.validators import validate_positive_id

from . import exceptions

PROFILE_FIELDS = business_profiles_db.BUSINESS_PROFILE_FIELDS
TEXT_PROFILE_FIELDS = tuple(
    field
    for field in PROFILE_FIELDS
    if field != "default_payment_terms_days"
)


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()
    return value or None


def _empty_profile(workspace_id: int) -> dict:
    return {
        "id": None,
        "workspace_id": workspace_id,
        **{field: None for field in PROFILE_FIELDS},
        "created_at": None,
        "updated_at": None,
    }


def _to_dict(profile: business_profiles_db.BusinessProfile) -> dict:
    return {
        "id": profile.id,
        "workspace_id": profile.workspace_id,
        "business_name": profile.business_name,
        "email": profile.email,
        "phone": profile.phone,
        "website": profile.website,
        "address_line1": profile.address_line1,
        "address_line2": profile.address_line2,
        "city": profile.city,
        "state": profile.state,
        "postal_code": profile.postal_code,
        "default_payment_terms_days": profile.default_payment_terms_days,
        "ways_to_pay": profile.ways_to_pay,
        "default_tax_rate": profile.default_tax_rate,
        "default_invoice_footer": profile.default_invoice_footer,
        "logo_url": profile.logo_url,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


def get_business_profile(cursor, *, workspace_id: int) -> dict:
    try:
        validate_positive_id(workspace_id, "Workspace id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    profile = business_profiles_db.get_business_profile(
        cursor,
        workspace_id=workspace_id,
    )
    return _to_dict(profile) if profile is not None else _empty_profile(workspace_id)


def save_business_profile(cursor, *, workspace_id: int, profile_data: dict) -> dict:
    try:
        validate_positive_id(workspace_id, "Workspace id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    normalized_data = {
        field: _normalize_optional_text(profile_data.get(field))
        for field in TEXT_PROFILE_FIELDS
    }
    normalized_data["default_payment_terms_days"] = profile_data.get(
        "default_payment_terms_days"
    )

    profile = business_profiles_db.upsert_business_profile(
        cursor,
        workspace_id=workspace_id,
        profile_data=normalized_data,
    )
    return _to_dict(profile)
