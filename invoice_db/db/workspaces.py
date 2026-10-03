from dataclasses import dataclass
from sqlite3 import Row


@dataclass
class Workspace:
    id: int
    name: str
    owner_user_id: int
    created_at: str
    updated_at: str


def _to_workspace(row: Row) -> Workspace:
    return Workspace(
        id=row["id"],
        name=row["name"],
        owner_user_id=row["owner_user_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_workspace(cursor, *, owner_user_id: int, name: str) -> int:
    cursor.execute(
        """
        INSERT INTO workspaces (owner_user_id, name)
        VALUES (?, ?)
        """,
        (owner_user_id, name.strip()),
    )
    return cursor.lastrowid


def get_workspace_by_owner_user_id(cursor, owner_user_id: int) -> Workspace | None:
    cursor.execute(
        "SELECT * FROM workspaces WHERE owner_user_id = ? ORDER BY id LIMIT 1",
        (owner_user_id,),
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
