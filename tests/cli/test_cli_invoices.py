from invoice_db.cli.app import app

# CRUD
def test_invoices_help_commands(runner):
    result = runner.invoke(app, ["invoices", "--help"])
    assert result.exit_code == 0
    expected_commands = ["add-tag", "create", "list", "get", "count", "remove-tag", "tags", "update", "delete"]
    for cmd in expected_commands:
        assert cmd in result.stdout

def test_create_and_get_invoice(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert f"id={invoice_john}" in result.stdout

def test_invoice_update(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "update", "--id", str(invoice_john), "--date-due", "2026-07-20", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert f"id={invoice_john}" in result.stdout
    assert "2026-07-20" in result.stdout

def test_invoice_list_all(customer_john, invoice_john, customer_alice, invoice_alice, runner, temp_db):
    result = runner.invoke(app, ["invoices", "list", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert str(invoice_john) in result.stdout
    assert str(invoice_alice) in result.stdout

def test_invoice_list_one_customer(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "create", "--customer-id", str(customer_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    result = runner.invoke(app, ["invoices", "list", "--customer-id", str(customer_john), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert str(invoice_john) in result.stdout, result.stdout

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

def test_invoice_set_status_rejects_manual_sent_to_paid(customer_john, invoice_john, runner, temp_db):
    sent_result = runner.invoke(
        app,
        [
            "invoices",
            "set-status",
            "--id",
            str(invoice_john),
            "--status",
            "sent",
            "--db",
            temp_db,
        ],
    )
    assert sent_result.exit_code == 0, sent_result.stdout

    paid_result = runner.invoke(
        app,
        [
            "invoices",
            "set-status",
            "--id",
            str(invoice_john),
            "--status",
            "paid",
            "--db",
            temp_db,
        ],
    )

    assert paid_result.exit_code == 1, paid_result.stdout
    assert "Invalid transition sent -> paid" in paid_result.stdout


def test_invoice_add_list_and_remove_tag(invoice_john, tag_repair, runner, temp_db):
    add_result = runner.invoke(app, [
        "invoices",
        "add-tag",
        "--invoice-id",
        str(invoice_john),
        "--tag-id",
        str(tag_repair),
        "--db",
        temp_db,
    ])
    assert add_result.exit_code == 0, add_result.stdout

    list_result = runner.invoke(app, [
        "invoices",
        "tags",
        "--invoice-id",
        str(invoice_john),
        "--db",
        temp_db,
    ])
    assert list_result.exit_code == 0, list_result.stdout
    assert "Repair" in list_result.stdout

    remove_result = runner.invoke(app, [
        "invoices",
        "remove-tag",
        "--invoice-id",
        str(invoice_john),
        "--tag-id",
        str(tag_repair),
        "--db",
        temp_db,
    ])
    assert remove_result.exit_code == 0, remove_result.stdout

    list_result = runner.invoke(app, [
        "invoices",
        "tags",
        "--invoice-id",
        str(invoice_john),
        "--db",
        temp_db,
    ])
    assert "No tags found" in list_result.stdout


def test_invoice_add_duplicate_tag_fails(invoice_john, tag_repair, runner, temp_db):
    first_result = runner.invoke(app, [
        "invoices",
        "add-tag",
        "--invoice-id",
        str(invoice_john),
        "--tag-id",
        str(tag_repair),
        "--db",
        temp_db,
    ])
    assert first_result.exit_code == 0, first_result.stdout

    duplicate_result = runner.invoke(app, [
        "invoices",
        "add-tag",
        "--invoice-id",
        str(invoice_john),
        "--tag-id",
        str(tag_repair),
        "--db",
        temp_db,
    ])

    assert duplicate_result.exit_code == 1, duplicate_result.stdout
    assert "already attached" in duplicate_result.stdout

# Negative Test
def test_create_invoice_invalid_customer_fails(customer_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "create", "--customer-id", "9999", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Customer not found" in result.stdout

def test_get_invoice_invalid_id_fails(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "get", "--id", "9999", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Invoice not found" in result.stdout

def test_update_invoice_no_fields_fails(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "update", "--id", str(invoice_john), "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Please enter one" in result.stdout

def test_update_invalid_invoice_id_fails(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "update", "--id", "9999", "--date-due", "2026-07-20", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Invoice not found" in result.stdout

def test_delete_invoice_invalid_fails(customer_john, invoice_john, runner, temp_db):
    result = runner.invoke(app, ["invoices", "delete", "--id", "9999", "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Invoice not found" in result.stdout
