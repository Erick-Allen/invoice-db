from invoice_db.cli.app import app
import sqlite3

def test_cli_help_commands(runner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    expected_commands = ["customers", "invoices", "product-categories", "products", "tags", "db"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_cli_version(runner):
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "customer_invoice_db CLI version" in result.stdout

def test_db_help_commands(runner):
    result = runner.invoke(app, ["db", "--help"])
    assert result.exit_code == 0
    expected_commands = ["init", "drop", "delete"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_db_drop_removes_all_schema_objects(runner, temp_db):
    result = runner.invoke(app, ["db", "drop", "--db", temp_db])

    assert result.exit_code == 0, result.stdout

    with sqlite3.connect(temp_db) as connect:
        remaining = connect.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type IN ('table', 'view')
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()

    assert remaining == []
