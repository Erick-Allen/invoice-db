from invoice_db.cli.app import app

CUSTOMER_JOHN_EMAIL = "john@test.com"

# CRUD
def test_customers_help_commands(runner):
    result = runner.invoke(app, ["customers", "--help"])
    assert result.exit_code == 0
    expected_commands = ["create", "delete", "get", "list", "update"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_create_and_get_customer(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "get", "--email", CUSTOMER_JOHN_EMAIL, "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "John" in result.stdout

def test_customer_update(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "update", "--email", CUSTOMER_JOHN_EMAIL, "--name", "Tommy", "--new-email", "tommy@test.com", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["customers", "get", "--email", "tommy@test.com", "--db", temp_db])
    assert "Tommy" in result.stdout
    assert "tommy@test.com" in result.stdout

    result = runner.invoke(app, ["customers", "get", "--email", CUSTOMER_JOHN_EMAIL, "--db", temp_db])
    assert "Customer not found" in result.stdout

def test_customer_list(customer_john, customer_alice, runner, temp_db):
    result = runner.invoke(app, ["customers", "list", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "John" in result.stdout
    assert "Alice" in result.stdout

def test_customer_delete(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "delete", "--id", str(customer_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["customers", "get", "--email", CUSTOMER_JOHN_EMAIL, "--db", temp_db])
    assert "Customer not found" in result.stdout


# Negative Tests
def test_create_customer_duplicate_email_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "create", "--name", "Johnny", "--email", CUSTOMER_JOHN_EMAIL, "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "already exists" in result.stdout

def test_customer_get_invalid_id_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "get", "--id", "-9999", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Customer not found" in result.stdout

def test_customer_update_no_fields_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "update", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "provide either --id or --email" in result.stdout

def test_customer_update_invalid_id_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "update", "--id", "-9999", "--name", "tommy", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Customer not found" in result.stdout

def test_customer_delete_invalid_id_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["customers", "delete", "--id", "-9999", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Customer not found" in result.stdout

# Invoice
