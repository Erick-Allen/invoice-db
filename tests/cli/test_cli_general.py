from invoice_db.cli.app import app

def test_cli_help_commands(runner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    expected_commands = ["--version", "customers", "invoices", "db"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_db_help_commands(runner):
    result = runner.invoke(app, ["db", "--help"])
    assert result.exit_code == 0
    expected_commands = ["init", "drop", "delete"]
    for cmd in expected_commands:
        assert cmd in result.stdout