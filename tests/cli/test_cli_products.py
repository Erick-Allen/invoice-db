from invoice_db.cli.app import app


def test_products_help_commands(runner):
    result = runner.invoke(app, ["products", "--help"])
    assert result.exit_code == 0
    expected_commands = ["add", "delete", "deactivate", "get", "list", "update"]
    for cmd in expected_commands:
        assert cmd in result.stdout


def test_add_and_get_product(product_widget, runner, temp_db):
    result = runner.invoke(app, ["products", "get", "--id", str(product_widget), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Widget" in result.stdout
    assert "$12.34" in result.stdout


def test_list_products(product_widget, product_service, runner, temp_db):
    result = runner.invoke(app, ["products", "list", "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Widget" in result.stdout
    assert "Service" in result.stdout


def test_update_product(product_widget, runner, temp_db):
    result = runner.invoke(app, [
        "products",
        "update",
        "--id",
        str(product_widget),
        "--name",
        "Updated Widget",
        "--price",
        "20",
        "--db",
        temp_db,
    ])

    assert result.exit_code == 0, result.stdout
    assert "Updated Widget" in result.stdout
    assert "$20.00" in result.stdout


def test_deactivate_product(product_widget, runner, temp_db):
    result = runner.invoke(app, ["products", "deactivate", "--id", str(product_widget), "--db", temp_db])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, ["products", "list", "--active-only", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Widget" not in result.stdout


def test_delete_product(product_widget, runner, temp_db):
    result = runner.invoke(app, ["products", "delete", "--id", str(product_widget), "--db", temp_db])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, ["products", "get", "--id", str(product_widget), "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Product not found" in result.stdout


def test_add_product_invalid_name_fails(runner, temp_db):
    result = runner.invoke(app, ["products", "add", "--name", " ", "--price", "10", "--db", temp_db])

    assert result.exit_code == 1, result.stdout
    assert "Product name cannot be empty" in result.stdout
