from invoice_db.db import workspaces as workspaces_db
from invoice_db.db.validators import validate_positive_id

from . import exceptions


def _as_validation_error(error: ValueError) -> exceptions.ValidationError:
    return exceptions.ValidationError(str(error))


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

    return {
        "id": workspace.id,
        "name": workspace.name,
        "owner_user_id": workspace.owner_user_id,
        "created_at": workspace.created_at,
        "updated_at": workspace.updated_at,
    }
