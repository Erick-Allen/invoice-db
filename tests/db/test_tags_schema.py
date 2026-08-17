import sqlite3

import pytest


def test_tags_table_exists(cursor):
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'tags'"
    ).fetchone()

    assert row is not None


def test_tags_columns(cursor):
    columns = {
        row["name"]: row
        for row in cursor.execute("PRAGMA table_info(tags)").fetchall()
    }

    assert set(columns) == {
        "id",
        "name",
        "description",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert columns["is_active"]["dflt_value"] == "1"


def test_tags_indexes(cursor):
    indexes = {
        row["name"]
        for row in cursor.execute("PRAGMA index_list(tags)").fetchall()
    }

    assert "idx_tags_name_nocase" in indexes
    assert "idx_tags_is_active" in indexes


def test_tags_reject_duplicate_names_case_insensitive(cursor):
    cursor.execute("INSERT INTO tags (name) VALUES (?)", ("Commercial",))

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO tags (name) VALUES (?)", ("commercial",))


def test_invoice_tags_table_exists(cursor):
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'invoice_tags'"
    ).fetchone()

    assert row is not None


def test_invoice_tags_columns(cursor):
    columns = {
        row["name"]: row
        for row in cursor.execute("PRAGMA table_info(invoice_tags)").fetchall()
    }

    assert set(columns) == {
        "invoice_id",
        "tag_id",
        "created_at",
    }


def test_invoice_tags_foreign_keys(cursor):
    foreign_keys = cursor.execute("PRAGMA foreign_key_list(invoice_tags)").fetchall()

    by_table = {row["table"]: row for row in foreign_keys}

    assert by_table["invoices"]["from"] == "invoice_id"
    assert by_table["invoices"]["on_delete"] == "CASCADE"
    assert by_table["tags"]["from"] == "tag_id"
    assert by_table["tags"]["on_delete"] == "RESTRICT"


def test_invoice_tags_indexes(cursor):
    indexes = {
        row["name"]
        for row in cursor.execute("PRAGMA index_list(invoice_tags)").fetchall()
    }

    assert "idx_invoice_tags_invoice_id" in indexes
    assert "idx_invoice_tags_tag_id" in indexes


def test_invoice_tags_reject_duplicate_invoice_tag_pair(cursor, invoice_john):
    cursor.execute("INSERT INTO tags (name) VALUES (?)", ("Repair",))
    tag_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO invoice_tags (invoice_id, tag_id) VALUES (?, ?)",
        (invoice_john, tag_id),
    )

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO invoice_tags (invoice_id, tag_id) VALUES (?, ?)",
            (invoice_john, tag_id),
        )


def test_invoice_tags_cascade_when_invoice_deleted(cursor, invoice_john):
    cursor.execute("INSERT INTO tags (name) VALUES (?)", ("Repair",))
    tag_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO invoice_tags (invoice_id, tag_id) VALUES (?, ?)",
        (invoice_john, tag_id),
    )

    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_john,))

    row = cursor.execute(
        "SELECT * FROM invoice_tags WHERE invoice_id = ?",
        (invoice_john,),
    ).fetchone()
    assert row is None


def test_invoice_tags_restrict_when_tag_has_invoices(cursor, invoice_john):
    cursor.execute("INSERT INTO tags (name) VALUES (?)", ("Repair",))
    tag_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO invoice_tags (invoice_id, tag_id) VALUES (?, ?)",
        (invoice_john, tag_id),
    )

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
