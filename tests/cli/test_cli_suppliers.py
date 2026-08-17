from invoice_db.cli.app import app


def test_suppliers_help_commands(runner):
    result = runner.invoke(app, ["suppliers", "--help"])
    assert result.exit_code == 0
    expected_commands = [
        "add",
        "delete",
        "deactivate",
        "get",
        "list",
        "products",
        "remove-from-products",
        "update",
    ]
    for cmd in expected_commands:
        assert cmd in result.stdout


def test_add_and_get_supplier(supplier_johnstone, runner, temp_db):
    result = runner.invoke(app, ["suppliers", "get", "--id", str(supplier_johnstone), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Johnstone" in result.stdout
    assert "555-0100" in result.stdout


def test_list_suppliers(supplier_johnstone, runner, temp_db):
    result = runner.invoke(app, ["suppliers", "list", "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Johnstone" in result.stdout


def test_update_supplier(supplier_johnstone, runner, temp_db):
    result = runner.invoke(app, [
        "suppliers",
        "update",
        "--id",
        str(supplier_johnstone),
        "--name",
        "Home Depot",
        "--website",
        "https://example.com",
        "--db",
        temp_db,
    ])

    assert result.exit_code == 0, result.stdout
    assert "Home Depot" in result.stdout
    assert "https://example.com" in result.stdout


def test_deactivate_supplier(supplier_johnstone, runner, temp_db):
    result = runner.invoke(app, ["suppliers", "deactivate", "--id", str(supplier_johnstone), "--db", temp_db])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, ["suppliers", "list", "--active-only", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Johnstone" not in result.stdout


def test_delete_unused_supplier(supplier_johnstone, runner, temp_db):
    result = runner.invoke(app, ["suppliers", "delete", "--id", str(supplier_johnstone), "--db", temp_db])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, ["suppliers", "get", "--id", str(supplier_johnstone), "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Supplier not found" in result.stdout


def test_add_duplicate_supplier_fails_with_clear_message(supplier_johnstone, runner, temp_db):
    result = runner.invoke(app, ["suppliers", "add", "--name", "johnstone", "--db", temp_db])

    assert result.exit_code == 1, result.stdout
    assert 'A supplier named "Johnstone" already exists.' in result.stdout


def test_product_supplier_attach_list_and_remove(product_widget, supplier_johnstone, runner, temp_db):
    result = runner.invoke(app, [
        "products",
        "add-supplier",
        "--product-id",
        str(product_widget),
        "--supplier-id",
        str(supplier_johnstone),
        "--note",
        "Counter pickup",
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    assert "Counter pickup" in result.stdout

    result = runner.invoke(app, [
        "products",
        "list-suppliers",
        "--product-id",
        str(product_widget),
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    assert "Johnstone" in result.stdout

    result = runner.invoke(app, [
        "products",
        "remove-supplier",
        "--product-id",
        str(product_widget),
        "--supplier-id",
        str(supplier_johnstone),
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, [
        "products",
        "list-suppliers",
        "--product-id",
        str(product_widget),
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    assert "No suppliers found" in result.stdout


def test_supplier_products_and_delete_restriction(product_widget, supplier_johnstone, runner, temp_db):
    result = runner.invoke(app, [
        "products",
        "add-supplier",
        "--product-id",
        str(product_widget),
        "--supplier-id",
        str(supplier_johnstone),
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, ["suppliers", "products", "--id", str(supplier_johnstone), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Widget" in result.stdout

    result = runner.invoke(app, ["suppliers", "delete", "--id", str(supplier_johnstone), "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert 'Cannot delete supplier "Johnstone"' in result.stdout


def test_remove_inactive_supplier_from_all_products(product_widget, supplier_johnstone, runner, temp_db):
    result = runner.invoke(app, [
        "products",
        "add-supplier",
        "--product-id",
        str(product_widget),
        "--supplier-id",
        str(supplier_johnstone),
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, ["suppliers", "deactivate", "--id", str(supplier_johnstone), "--db", temp_db])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, [
        "suppliers",
        "remove-from-products",
        "--id",
        str(supplier_johnstone),
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    assert "Removed supplier" in result.stdout
    assert "1 products" in result.stdout

    result = runner.invoke(app, ["suppliers", "delete", "--id", str(supplier_johnstone), "--db", temp_db])
    assert result.exit_code == 0, result.stdout
