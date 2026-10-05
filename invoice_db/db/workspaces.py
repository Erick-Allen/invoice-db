from dataclasses import dataclass
from sqlite3 import Row


@dataclass
class Workspace:
    id: int
    name: str
    owner_user_id: int
    is_guest: bool
    expires_at: str | None
    created_at: str
    updated_at: str


def _to_workspace(row: Row) -> Workspace:
    return Workspace(
        id=row["id"],
        name=row["name"],
        owner_user_id=row["owner_user_id"],
        is_guest=bool(row["is_guest"]),
        expires_at=row["expires_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_workspace(
    cursor,
    *,
    owner_user_id: int,
    name: str,
    is_guest: bool = False,
    expires_at: str | None = None,
) -> int:
    cursor.execute(
        """
        INSERT INTO workspaces (owner_user_id, name, is_guest, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (owner_user_id, name.strip(), int(is_guest), expires_at),
    )
    return cursor.lastrowid


def get_workspace_by_owner_user_id(cursor, owner_user_id: int) -> Workspace | None:
    cursor.execute(
        "SELECT * FROM workspaces WHERE owner_user_id = ? ORDER BY id LIMIT 1",
        (owner_user_id,),
    )
    row = cursor.fetchone()
    return _to_workspace(row) if row else None


def get_workspace_by_id(cursor, workspace_id: int) -> Workspace | None:
    cursor.execute(
        "SELECT * FROM workspaces WHERE id = ?",
        (workspace_id,),
    )
    row = cursor.fetchone()
    return _to_workspace(row) if row else None


def get_or_create_default_workspace(cursor, *, owner_user_id: int, name: str) -> Workspace:
    workspace = get_workspace_by_owner_user_id(cursor, owner_user_id)
    if workspace is not None:
        return workspace

    workspace_id = create_workspace(cursor, owner_user_id=owner_user_id, name=name)
    workspace = get_workspace_by_owner_user_id(cursor, owner_user_id)
    if workspace is None:
        raise RuntimeError(f"Workspace was not created (id={workspace_id}).")
    return workspace


def update_guest_expiration(cursor, *, workspace_id: int, expires_at: str) -> None:
    cursor.execute(
        """
        UPDATE workspaces
        SET expires_at = ?
        WHERE id = ? AND is_guest = 1
        """,
        (expires_at, workspace_id),
    )


def get_expired_guest_workspace_owner_ids(cursor, *, now: str) -> list[int]:
    cursor.execute(
        """
        SELECT owner_user_id
        FROM workspaces
        WHERE is_guest = 1
          AND expires_at IS NOT NULL
          AND expires_at <= ?
        """,
        (now,),
    )
    return [row["owner_user_id"] for row in cursor.fetchall()]


def delete_expired_guest_workspaces(cursor, *, now: str) -> int:
    cursor.execute(
        """
        DELETE FROM workspaces
        WHERE is_guest = 1
          AND expires_at IS NOT NULL
          AND expires_at <= ?
        """,
        (now,),
    )
    return cursor.rowcount
