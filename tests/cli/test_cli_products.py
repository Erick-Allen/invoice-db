from invoice_db.cli.app import app


def test_products_help_commands(runner):
    result = runner.invoke(app, ["products", "--help"])
    assert result.exit_code == 0
    expected_commands = [
        "add",
        "add-supplier",
        "delete",
        "deactivate",
        "get",
        "list",
        "list-suppliers",
        "remove-supplier",
        "update",
    ]
    for cmd in expected_commands:
        assert cmd in result.stdout


def test_add_and_get_product(product_widget, runner, temp_db):
    result = runner.invoke(app, ["products", "get", "--id", str(product_widget), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Widget" in result.stdout
    assert "Uncategorized" in result.stdout
    assert "$9.00" in result.stdout
    assert "$12.34" in result.stdout


def test_list_products(product_widget, product_service, runner, temp_db):
    result = runner.invoke(app, ["products", "list", "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Widget" in result.stdout
    assert "Service" in result.stdout


def test_update_product(product_widget, runner, temp_db):
    category_result = runner.invoke(app, [
        "product-categories",
        "add",
        "--name",
        "Labor",
        "--db",
        temp_db,
    ])
    assert category_result.exit_code == 0, category_result.stdout
    category_id = int(category_result.stdout.split("id=")[1].split(")")[0])

    result = runner.invoke(app, [
        "products",
        "update",
        "--id",
        str(product_widget),
        "--name",
        "Updated Widget",
        "--price",
        "20",
        "--cost",
        "8.50",
        "--category-id",
        str(category_id),
        "--db",
        temp_db,
    ])

    assert result.exit_code == 0, result.stdout
    assert "Updated Widget" in result.stdout
    assert "Labor" in result.stdout
    assert "$8.50" in result.stdout
    assert "$20.00" in result.stdout


def test_add_product_with_category(runner, temp_db):
    category_result = runner.invoke(app, [
        "product-categories",
        "add",
        "--name",
        "Materials",
        "--db",
        temp_db,
    ])
    assert category_result.exit_code == 0, category_result.stdout
    category_id = int(category_result.stdout.split("id=")[1].split(")")[0])

    result = runner.invoke(app, [
        "products",
        "add",
        "--name",
        "Cable",
        "--price",
        "12",
        "--cost",
        "7.25",
        "--category-id",
        str(category_id),
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout

    list_result = runner.invoke(app, ["products", "list", "--db", temp_db])
    assert list_result.exit_code == 0, list_result.stdout
    assert "Cable" in list_result.stdout
    assert "Materials" in list_result.stdout
    assert "$7.25" in list_result.stdout


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
