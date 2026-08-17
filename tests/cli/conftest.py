import re
import pytest
from invoice_db.cli.app import app
from typer.testing import CliRunner


CUSTOMER_ID_REGEX = re.compile(r"id=(\d+)")
INVOICE_ID_REGEX = re.compile(r"Created invoice \(id=(\d+)\)")
PRODUCT_ID_REGEX = re.compile(r"id=(\d+)")
TAG_ID_REGEX = re.compile(r"id=(\d+)")

#CLI fixtures
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
    result = runner.invoke(app, [
        "customers", "create", 
        "--name", "John", 
        "--email", "john@test.com", 
        "--db", temp_db
    ])
    assert result.exit_code == 0, result.stdout
    match = CUSTOMER_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse customer id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def customer_alice(runner, temp_db):
    result = runner.invoke(app, [
        "customers", "create", 
        "--name", "Alice", 
        "--email", "alice@test.com", 
        "--db", temp_db
    ])
    assert result.exit_code == 0, result.stdout
    match = CUSTOMER_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse customer id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def invoice_john(runner, temp_db, customer_john):
    result = runner.invoke(app, [
        "invoices", "create", 
        "--customer-id", str(customer_john), 
        "--db", temp_db
    ])
    assert result.exit_code == 0, result.stdout
    match = INVOICE_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse invoice id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def invoice_alice(runner, temp_db, customer_alice):
    result = runner.invoke(app, [
        "invoices", "create", 
        "--customer-id", str(customer_alice), 
        "--db", temp_db
    ])
    assert result.exit_code == 0, result.stdout
    match = INVOICE_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse invoice id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def product_widget(runner, temp_db):
    result = runner.invoke(app, [
        "products",
        "add",
        "--name",
        "Widget",
        "--price",
        "12.34",
        "--cost",
        "9",
        "--description",
        "A test widget",
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    match = PRODUCT_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse product id from output: {result.stdout}"
    return int(match.group(1))

@pytest.fixture
def product_service(runner, temp_db):
    result = runner.invoke(app, [
        "products",
        "add",
        "--name",
        "Service",
        "--price",
        "25",
        "--cost",
        "0",
        "--description",
        "A test service",
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    match = PRODUCT_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse product id from output: {result.stdout}"
    return int(match.group(1))


@pytest.fixture
def tag_repair(runner, temp_db):
    result = runner.invoke(app, [
        "tags",
        "add",
        "--name",
        "Repair",
        "--description",
        "Repair work",
        "--db",
        temp_db,
    ])
    assert result.exit_code == 0, result.stdout
    match = TAG_ID_REGEX.search(result.stdout)
    assert match, f"Could not parse tag id from output: {result.stdout}"
    return int(match.group(1))
