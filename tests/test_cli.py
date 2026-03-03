import re
import pytest
from typer.testing import CliRunner

from invoice_db.cli import app

customer_ID_REGEX = re.compile(r"id=(\d+)")
INVOICE_ID_REGEX = re.compile(r"Invoice\s+(\d+)")

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_db(runner, tmp_path):
    db_path = tmp_path / "test.db"
    result = runner.invoke(app, ["db", "init", "--db", str(db_path)])
    assert result.exit_code == 0, result.stdout
    return str(db_path)

@pytest.fixture
def customer_john(runner, temp_db):
    result = runner.invoke(app, ["customers", "create", "--name", "John", "--email", "john@test.com", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    match = customer_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse customer id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def customer_alice(runner, temp_db):
    result = runner.invoke(app, ["customers", "create", "--name", "Alice", "--email", "alice@test.com", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    match = customer_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse customer id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def invoice_john(runner, temp_db, customer_john):
    result = runner.invoke(app, ["invoices", "create", "--id", str(customer_john), "--total", "1234", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    match = INVOICE_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse invoice id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def invoice_alice(runner, temp_db, customer_alice):
    result = runner.invoke(app, ["invoices", "create", "--id", str(customer_alice), "--total", "9999", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    match = INVOICE_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse invoice id from output: {result.stdout}"
    return int(match.group(1))

# Interface Tests
def test_cli_help_commands(runner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    expected_commands = ["--version", "customers", "invoices", "db"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_customers_help_commands(runner):
    result = runner.invoke(app, ["customers", "--help"])
    assert result.exit_code == 0
    expected_commands = ["create", "delete", "get", "list", "update"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_invoices_help_commands(runner):
    result = runner.invoke(app, ["invoices", "--help"])
    assert result.exit_code == 0
    expected_commands = ["create", "list", "get", "count", "update", "delete"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_db_help_commands(runner):
    result = runner.invoke(app, ["db", "--help"])
    assert result.exit_code == 0
    expected_commands = ["init", "drop", "delete"]
    for cmd in expected_commands:
        assert cmd in result.stdout

# Behavorial (Integration) Tests

# customer
def test_create_and_get_customer(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "get", "--email", "john@test.com", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "John" in result.stdout

def test_customer_update(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "update", "--email", "john@test.com", "--name", "Tommy", "--new-email", "tommy@gmail.com", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["customers", "get", "--email", "tommy@gmail.com", "--db", temp_db])
    assert "Tommy" in result.stdout
    assert "tommy@gmail.com" in result.stdout

    result = runner.invoke(app, ["customers", "get", "--email", "john@test.com", "--db", temp_db])
    assert "customer not found" in result.stdout

def test_customer_list(customer_john, customer_alice, runner, temp_db):
    result = runner.invoke(app, ["customers", "list", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "John" in result.stdout
    assert "Alice" in result.stdout

def test_customer_delete(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "delete", "--id", str(customer_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["customers", "get", "--email", "john@test.com", "--db", temp_db])
    assert "customer not found" in result.stdout

#Invoice
def test_create_and_get_invoice(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert f"id={invoice_john}" in result.stdout

def test_invoice_update(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "update", "--id", str(invoice_john), "--total", "9876", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert f"id={invoice_john}" in result.stdout
    assert "9876" in result.stdout

def test_invoice_list_all(customer_john, invoice_john, customer_alice, invoice_alice, runner, temp_db):
    result = runner.invoke(app, ["invoices", "list", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "1234" in result.stdout
    assert "9999" in result.stdout

def test_invoice_list_one_customer(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "create", "--id", str(customer_john), "--total", "777", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["invoices", "list", "--customer-id", str(customer_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "1234" in result.stdout, result.stdout
    assert "777" in result.stdout, result.stdout

def test_invoice_count_all(customer_john, invoice_john, customer_alice, invoice_alice, runner, temp_db):
    result = runner.invoke(app, ["invoices", "count", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "number of invoices: 2" in result.stdout

def test_invoice_count_one_customer(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "count", "--customer-id", str(customer_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Invoices for John" in result.stdout

def test_invoice_delete(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "delete", "--id", str(invoice_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert "Invoice not found" in result.stdout

# Negative Tests

# customer
def test_create_customer_duplicate_email_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "create", "--name", "Johnny", "--email", "john@test.com", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "already exists" in result.stdout

def test_customer_get_invalid_id_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "get", "--id", "-9999", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "customer not found" in result.stdout


def test_customer_update_no_fields_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "update", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "provide either --id or --email" in result.stdout

def test_customer_update_invalid_id_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "update", "--id", "-9999", "--name", "tommy", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "customer not found" in result.stdout

def test_customer_delete_invalid_id_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "delete", "--id", "-9999", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "customer not found" in result.stdout

# Invoice
def test_create_invoice_invalid_customer_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "create", "--id", "-9999", "--total", "1234", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "customer not found" in result.stdout

def test_get_invoice_invalid_id_fails(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "get", "--id", "-9999", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Invoice not found" in result.stdout

def test_update_invoice_no_fields_fails(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "update", "--id", str(invoice_john), "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Please enter one" in result.stdout

def test_update_invalid_invoice_id_fails(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "update", "--id", "-9999", "--total", "1234", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Invoice not found" in result.stdout

def test_delete_invoice_invalid_fails(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "delete", "--id", "-9999", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Invoice not found" in result.stdout