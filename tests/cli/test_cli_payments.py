import re

from invoice_db.cli.app import app


PAYMENT_ID_REGEX = re.compile(r"Created payment \(id=(\d+)\)")


def make_sent_invoice_with_total(runner, temp_db, invoice_id, product_id):
    item_result = runner.invoke(app, [
        "invoice-items",
        "add",
        "--invoice-id",
        str(invoice_id),
        "--product-id",
        str(product_id),
        "--db",
        temp_db,
    ])
    assert item_result.exit_code == 0, item_result.stdout

    status_result = runner.invoke(app, [
        "invoices",
        "set-status",
        "--id",
        str(invoice_id),
        "--status",
        "sent",
        "--db",
        temp_db,
    ])
    assert status_result.exit_code == 0, status_result.stdout


def add_payment(runner, temp_db, invoice_id, *extra_args):
    result = runner.invoke(app, [
        "payments",
        "add",
        "--invoice-id",
        str(invoice_id),
        "--amount",
        "5.00",
        "--payment-date",
        "2026-06-17",
        "--method",
        "cash",
        "--db",
        temp_db,
        *extra_args,
    ])
    assert result.exit_code == 0, result.stdout
    match = PAYMENT_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse payment id from output: {result.stdout}"
    return int(match.group(1))


def test_payments_help_commands(runner):
    result = runner.invoke(app, ["payments", "--help"])

    assert result.exit_code == 0
    expected_commands = ["add", "delete", "get", "list", "summary"]
    for cmd in expected_commands:
        assert cmd in result.stdout


def test_add_and_get_payment(runner, temp_db, invoice_john, product_widget):
    make_sent_invoice_with_total(runner, temp_db, invoice_john, product_widget)
    payment_id = add_payment(runner, temp_db, invoice_john)

    result = runner.invoke(app, ["payments", "get", "--id", str(payment_id), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert f"id={payment_id}" in result.stdout
    assert "$5.00" in result.stdout
    assert "cash" in result.stdout


def test_list_payments(runner, temp_db, invoice_john, product_widget):
    make_sent_invoice_with_total(runner, temp_db, invoice_john, product_widget)
    add_payment(runner, temp_db, invoice_john)

    result = runner.invoke(app, ["payments", "list", "--invoice-id", str(invoice_john), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Payments" in result.stdout
    assert "$5.00" in result.stdout


def test_payment_summary(runner, temp_db, invoice_john, product_widget):
    make_sent_invoice_with_total(runner, temp_db, invoice_john, product_widget)
    add_payment(runner, temp_db, invoice_john)

    result = runner.invoke(app, ["payments", "summary", "--invoice-id", str(invoice_john), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Payment Summary" in result.stdout
    assert "$12.34" in result.stdout
    assert "$5.00" in result.stdout
    assert "$7.34" in result.stdout


def test_full_payment_marks_invoice_paid(runner, temp_db, invoice_john, product_widget):
    make_sent_invoice_with_total(runner, temp_db, invoice_john, product_widget)

    result = runner.invoke(app, [
        "payments",
        "add",
        "--invoice-id",
        str(invoice_john),
        "--amount",
        "12.34",
        "--payment-date",
        "2026-06-17",
        "--method",
        "card",
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout

    invoice_result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert invoice_result.exit_code == 0, invoice_result.stdout
    assert "paid" in invoice_result.stdout


def test_delete_payment_reopens_paid_invoice(runner, temp_db, invoice_john, product_widget):
    make_sent_invoice_with_total(runner, temp_db, invoice_john, product_widget)
    payment_id = add_payment(runner, temp_db, invoice_john, "--amount", "12.34", "--method", "card")

    result = runner.invoke(app, ["payments", "delete", "--id", str(payment_id), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Deleted payment" in result.stdout
    assert "$12.34" in result.stdout

    invoice_result = runner.invoke(app, ["invoices", "get", "--id", str(invoice_john), "--db", temp_db])
    assert invoice_result.exit_code == 0, invoice_result.stdout
    assert "sent" in invoice_result.stdout


def test_add_payment_to_draft_invoice_fails(runner, temp_db, invoice_john):
    result = runner.invoke(app, [
        "payments",
        "add",
        "--invoice-id",
        str(invoice_john),
        "--amount",
        "5.00",
        "--payment-date",
        "2026-06-17",
        "--method",
        "cash",
        "--db",
        temp_db,
    ])

    assert result.exit_code == 1, result.stdout
    assert "Only sent invoices" in result.stdout


def test_add_payment_over_balance_fails(runner, temp_db, invoice_john, product_widget):
    make_sent_invoice_with_total(runner, temp_db, invoice_john, product_widget)

    result = runner.invoke(app, [
        "payments",
        "add",
        "--invoice-id",
        str(invoice_john),
        "--amount",
        "12.35",
        "--payment-date",
        "2026-06-17",
        "--method",
        "cash",
        "--db",
        temp_db,
    ])

    assert result.exit_code == 1, result.stdout
    assert "balance due" in result.stdout


def test_add_payment_with_invalid_method_fails(runner, temp_db, invoice_john, product_widget):
    make_sent_invoice_with_total(runner, temp_db, invoice_john, product_widget)

    result = runner.invoke(app, [
        "payments",
        "add",
        "--invoice-id",
        str(invoice_john),
        "--amount",
        "5.00",
        "--payment-date",
        "2026-06-17",
        "--method",
        "crypto",
        "--db",
        temp_db,
    ])

    assert result.exit_code == 1, result.stdout
    assert "Payment method" in result.stdout
