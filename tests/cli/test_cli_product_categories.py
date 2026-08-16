from invoice_db.cli.app import app


def _parse_id(output: str) -> int:
    return int(output.split("id=")[1].split(")")[0])


def test_product_categories_help_commands(runner):
    result = runner.invoke(app, ["product-categories", "--help"])
    assert result.exit_code == 0
    expected_commands = ["add", "deactivate", "delete", "list", "update"]
    for cmd in expected_commands:
        assert cmd in result.stdout


def test_list_product_categories_includes_default(runner, temp_db):
    result = runner.invoke(app, ["product-categories", "list", "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Uncategorized" in result.stdout


def test_add_and_update_product_category(runner, temp_db):
    result = runner.invoke(app, [
        "product-categories",
        "add",
        "--name",
        "Labor",
        "--description",
        "Billable work",
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    category_id = _parse_id(result.stdout)

    update_result = runner.invoke(app, [
        "product-categories",
        "update",
        "--id",
        str(category_id),
        "--name",
        "Services",
        "--db",
        temp_db,
    ])

    assert update_result.exit_code == 0, update_result.stdout
    assert "Services" in update_result.stdout
    assert "Billable work" in update_result.stdout


def test_deactivate_product_category(runner, temp_db):
    result = runner.invoke(app, [
        "product-categories",
        "add",
        "--name",
        "Materials",
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    category_id = _parse_id(result.stdout)

    deactivate_result = runner.invoke(app, [
        "product-categories",
        "deactivate",
        "--id",
        str(category_id),
        "--db",
        temp_db,
    ])
    assert deactivate_result.exit_code == 0, deactivate_result.stdout

    list_result = runner.invoke(app, ["product-categories", "list", "--active-only", "--db", temp_db])
    assert list_result.exit_code == 0, list_result.stdout
    assert "Materials" not in list_result.stdout


def test_delete_unused_product_category(runner, temp_db):
    result = runner.invoke(app, [
        "product-categories",
        "add",
        "--name",
        "Materials",
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    category_id = _parse_id(result.stdout)

    delete_result = runner.invoke(app, [
        "product-categories",
        "delete",
        "--id",
        str(category_id),
        "--db",
        temp_db,
    ])
    assert delete_result.exit_code == 0, delete_result.stdout

    list_result = runner.invoke(app, ["product-categories", "list", "--db", temp_db])
    assert list_result.exit_code == 0, list_result.stdout
    assert "Materials" not in list_result.stdout


def test_delete_category_with_products_fails(runner, temp_db):
    result = runner.invoke(app, [
        "product-categories",
        "add",
        "--name",
        "Materials",
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    category_id = _parse_id(result.stdout)

    product_result = runner.invoke(app, [
        "products",
        "add",
        "--name",
        "Cable",
        "--price",
        "12",
        "--category-id",
        str(category_id),
        "--db",
        temp_db,
    ])
    assert product_result.exit_code == 0, product_result.stdout

    delete_result = runner.invoke(app, [
        "product-categories",
        "delete",
        "--id",
        str(category_id),
        "--db",
        temp_db,
    ])

    assert delete_result.exit_code == 1, delete_result.stdout
    assert 'Cannot delete product category "Materials" because 1 product uses it.' in delete_result.stdout


def test_add_duplicate_product_category_fails_with_clear_message(runner, temp_db):
    result = runner.invoke(app, [
        "product-categories",
        "add",
        "--name",
        "Labor",
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout

    duplicate_result = runner.invoke(app, [
        "product-categories",
        "add",
        "--name",
        "labor",
        "--db",
        temp_db,
    ])

    assert duplicate_result.exit_code == 1, duplicate_result.stdout
    assert 'A product category named "Labor" already exists.' in duplicate_result.stdout


def test_add_product_category_invalid_name_fails(runner, temp_db):
    result = runner.invoke(app, ["product-categories", "add", "--name", " ", "--db", temp_db])

    assert result.exit_code == 1, result.stdout
    assert "Product category name cannot be empty" in result.stdout
