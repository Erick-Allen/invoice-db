import re

from invoice_db.cli.app import app


INVOICE_ITEM_ID_REGEX = re.compile(r"Created invoice item \(id=(\d+)\)")


def add_invoice_item(runner, temp_db, invoice_id, product_id, *extra_args):
    result = runner.invoke(app, [
        "invoice-items",
        "add",
        "--invoice-id",
        str(invoice_id),
        "--product-id",
        str(product_id),
        "--db",
        temp_db,
        *extra_args,
    ])
    assert result.exit_code == 0, result.stdout
    match = INVOICE_ITEM_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse invoice item id from output: {result.stdout}"
    return int(match.group(1))


def test_invoice_items_help_commands(runner):
    result = runner.invoke(app, ["invoice-items", "--help"])

    assert result.exit_code == 0
    expected_commands = ["add", "delete", "get", "list", "update"]
    for cmd in expected_commands:
        assert cmd in result.stdout


def test_add_and_get_invoice_item(runner, temp_db, invoice_john, product_widget):
    item_id = add_invoice_item(
        runner,
        temp_db,
        invoice_john,
        product_widget,
        "--quantity",
        "2",
        "--unit-cost",
        "8.50",
    )

    result = runner.invoke(app, ["invoice-items", "get", "--id", str(item_id), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert f"id={item_id}" in result.stdout
    assert "$8.50" in result.stdout
    assert "$17.00" in result.stdout
    assert "$12.34" in result.stdout
    assert "$24.68" in result.stdout


def test_list_invoice_items(runner, temp_db, invoice_john, product_widget, product_service):
    add_invoice_item(runner, temp_db, invoice_john, product_widget)
    add_invoice_item(runner, temp_db, invoice_john, product_service)

    result = runner.invoke(app, ["invoice-items", "list", "--invoice-id", str(invoice_john), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "$9.00" in result.stdout
    assert "$12.34" in result.stdout
    assert "$0.00" in result.stdout
    assert "$25.00" in result.stdout


def test_update_invoice_item(runner, temp_db, invoice_john, product_widget):
    item_id = add_invoice_item(runner, temp_db, invoice_john, product_widget)

    result = runner.invoke(app, [
        "invoice-items",
        "update",
        "--id",
        str(item_id),
        "--quantity",
        "3",
        "--unit-cost",
        "4",
        "--unit-price",
        "10",
        "--db",
        temp_db,
    ])

    assert result.exit_code == 0, result.stdout
    assert "$4.00" in result.stdout
    assert "$12.00" in result.stdout
    assert "$10.00" in result.stdout
    assert "$30.00" in result.stdout


def test_delete_invoice_item(runner, temp_db, invoice_john, product_widget):
    item_id = add_invoice_item(runner, temp_db, invoice_john, product_widget)

    result = runner.invoke(app, ["invoice-items", "delete", "--id", str(item_id), "--db", temp_db])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, ["invoice-items", "get", "--id", str(item_id), "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Invoice item not found" in result.stdout


def test_add_invoice_item_recalculates_invoice_total(runner, temp_db, invoice_john, product_widget):
    add_invoice_item(runner, temp_db, invoice_john, product_widget, "--quantity", "2")

    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "$24.68" in result.stdout


def test_get_invoice_includes_line_items(runner, temp_db, invoice_john, product_widget):
    item_id = add_invoice_item(runner, temp_db, invoice_john, product_widget, "--quantity", "2")

    result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Line Items" in result.stdout
    assert str(item_id) in result.stdout
    assert "$12.34" in result.stdout
    assert "$24.68" in result.stdout


def test_list_invoices_can_include_line_items(runner, temp_db, invoice_john, product_widget):
    add_invoice_item(runner, temp_db, invoice_john, product_widget, "--quantity", "2")

    result = runner.invoke(app, ["invoices", "list", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Line Items for Invoice" not in result.stdout

    result = runner.invoke(app, ["invoices", "list", "--include-items", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Line Items for Invoice" in result.stdout
    assert "$12.34" in result.stdout
    assert "$24.68" in result.stdout


def test_add_invoice_item_to_locked_invoice_fails(runner, temp_db, invoice_john, product_widget):
    status_result = runner.invoke(app, [
        "invoices",
        "set-status",
        "--id",
        str(invoice_john),
        "--status",
        "sent",
        "--db",
        temp_db,
    ])
    assert status_result.exit_code == 0, status_result.stdout

    result = runner.invoke(app, [
        "invoice-items",
        "add",
        "--invoice-id",
        str(invoice_john),
        "--product-id",
        str(product_widget),
        "--db",
        temp_db,
    ])

    assert result.exit_code == 1, result.stdout
    assert "cannot be changed" in result.stdout


def test_add_invoice_item_with_inactive_product_fails(runner, temp_db, invoice_john, product_widget):
    deactivate_result = runner.invoke(app, ["products", "deactivate", "--id", str(product_widget), "--db", temp_db])
    assert deactivate_result.exit_code == 0, deactivate_result.stdout

    result = runner.invoke(app, [
        "invoice-items",
        "add",
        "--invoice-id",
        str(invoice_john),
        "--product-id",
        str(product_widget),
        "--db",
        temp_db,
    ])

    assert result.exit_code == 1, result.stdout
    assert "Product is inactive" in result.stdout


def test_send_invoice_with_inactive_line_item_product_fails(runner, temp_db, invoice_john, product_widget):
    add_invoice_item(runner, temp_db, invoice_john, product_widget)

    deactivate_result = runner.invoke(app, ["products", "deactivate", "--id", str(product_widget), "--db", temp_db])
    assert deactivate_result.exit_code == 0, deactivate_result.stdout

    result = runner.invoke(app, [
        "invoices",
        "set-status",
        "--id",
        str(invoice_john),
        "--status",
        "sent",
        "--db",
        temp_db,
    ])

    assert result.exit_code == 1, result.stdout
    assert "inactive products" in result.stdout
    assert "Widget" in result.stdout
