from invoice_db.cli.app import app

# CRUD
def test_invoices_help_commands(runner):
    result = runner.invoke(app, ["invoices", "--help"])
    assert result.exit_code == 0
    expected_commands = ["create", "list", "get", "count", "update", "delete"]
    for cmd in expected_commands:
        assert cmd in result.stdout

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
    assert "2" in result.stdout

def test_invoice_count_one_customer(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "count", "--customer-id", str(customer_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "1" in result.stdout

def test_invoice_delete(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "delete", "--id", str(invoice_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert "Invoice not found" in result.stdout

# Negative Test
def test_create_invoice_invalid_customer_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "create", "--id", "-9999", "--total", "1234", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Customer not found" in result.stdout

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