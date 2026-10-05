from datetime import datetime, timedelta, timezone

from invoice_db.db import workspaces as workspaces_db
from invoice_db.db.validators import validate_positive_id

from . import exceptions

GUEST_WORKSPACE_TTL = timedelta(hours=24)


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


def _utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _guest_expires_at(now: datetime | None = None) -> str:
    base_time = now or datetime.now(timezone.utc)
    return _utc_timestamp(base_time + GUEST_WORKSPACE_TTL)


def _to_dict(workspace: workspaces_db.Workspace) -> dict:
    return {
        "id": workspace.id,
        "name": workspace.name,
        "owner_user_id": workspace.owner_user_id,
        "is_guest": workspace.is_guest,
        "expires_at": workspace.expires_at,
        "created_at": workspace.created_at,
        "updated_at": workspace.updated_at,
    }


def get_or_create_default_workspace(cursor, *, owner_user_id: int, owner_label: str) -> dict:
    try:
        validate_positive_id(owner_user_id, "Owner user id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    workspace_name = f"{owner_label}'s Workspace" if owner_label else "Personal Workspace"
    workspace = workspaces_db.get_or_create_default_workspace(
        cursor,
        owner_user_id=owner_user_id,
        name=workspace_name,
    )

    return _to_dict(workspace)


def create_guest_workspace(cursor, *, owner_user_id: int) -> dict:
    try:
        validate_positive_id(owner_user_id, "Owner user id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    workspace_id = workspaces_db.create_workspace(
        cursor,
        owner_user_id=owner_user_id,
        name="Guest Workspace",
        is_guest=True,
        expires_at=_guest_expires_at(),
    )
    workspace = workspaces_db.get_workspace_by_owner_user_id(cursor, owner_user_id)
    if workspace is None:
        raise RuntimeError(f"Guest workspace was not created (id={workspace_id}).")

    return _to_dict(workspace)


def get_workspace_for_owner(cursor, *, owner_user_id: int) -> dict | None:
    try:
        validate_positive_id(owner_user_id, "Owner user id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    workspace = workspaces_db.get_workspace_by_owner_user_id(cursor, owner_user_id)
    return _to_dict(workspace) if workspace is not None else None


def touch_guest_workspace(cursor, *, workspace_id: int) -> dict | None:
    try:
        validate_positive_id(workspace_id, "Workspace id")
    except ValueError as e:
        raise _as_validation_error(e) from e

    workspaces_db.update_guest_expiration(
        cursor,
        workspace_id=workspace_id,
        expires_at=_guest_expires_at(),
    )
    workspace = workspaces_db.get_workspace_by_id(cursor, workspace_id)
    return _to_dict(workspace) if workspace is not None else None


def delete_expired_guest_workspaces(cursor, *, now: datetime | None = None) -> list[int]:
    timestamp = _utc_timestamp(now or datetime.now(timezone.utc))
    owner_user_ids = workspaces_db.get_expired_guest_workspace_owner_ids(
        cursor,
        now=timestamp,
    )
    workspaces_db.delete_expired_guest_workspaces(cursor, now=timestamp)
    return owner_user_ids
