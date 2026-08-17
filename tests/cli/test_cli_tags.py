from invoice_db.cli.app import app


def test_tags_help_commands(runner):
    result = runner.invoke(app, ["tags", "--help"])
    assert result.exit_code == 0
    expected_commands = ["add", "delete", "deactivate", "get", "list", "update"]
    for cmd in expected_commands:
        assert cmd in result.stdout


def test_add_and_get_tag(tag_repair, runner, temp_db):
    result = runner.invoke(app, ["tags", "get", "--id", str(tag_repair), "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Repair" in result.stdout
    assert "Repair work" in result.stdout


def test_list_tags(tag_repair, runner, temp_db):
    result = runner.invoke(app, ["tags", "list", "--db", temp_db])

    assert result.exit_code == 0, result.stdout
    assert "Repair" in result.stdout


def test_update_tag(tag_repair, runner, temp_db):
    result = runner.invoke(app, [
        "tags",
        "update",
        "--id",
        str(tag_repair),
        "--name",
        "Roof",
        "--description",
        "Roof work",
        "--db",
        temp_db,
    ])

    assert result.exit_code == 0, result.stdout
    assert "Roof" in result.stdout
    assert "Roof work" in result.stdout


def test_deactivate_tag(tag_repair, runner, temp_db):
    result = runner.invoke(app, ["tags", "deactivate", "--id", str(tag_repair), "--db", temp_db])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, ["tags", "list", "--active-only", "--db", temp_db])
    assert result.exit_code == 0, result.stdout
    assert "Repair" not in result.stdout


def test_delete_unused_tag(tag_repair, runner, temp_db):
    result = runner.invoke(app, ["tags", "delete", "--id", str(tag_repair), "--db", temp_db])
    assert result.exit_code == 0, result.stdout

    result = runner.invoke(app, ["tags", "get", "--id", str(tag_repair), "--db", temp_db])
    assert result.exit_code == 1, result.stdout
    assert "Tag not found" in result.stdout


def test_add_duplicate_tag_fails_with_clear_message(tag_repair, runner, temp_db):
    result = runner.invoke(app, ["tags", "add", "--name", "repair", "--db", temp_db])

    assert result.exit_code == 1, result.stdout
    assert 'A tag named "Repair" already exists.' in result.stdout


def test_add_tag_invalid_name_fails(runner, temp_db):
    result = runner.invoke(app, ["tags", "add", "--name", " ", "--db", temp_db])

    assert result.exit_code == 1, result.stdout
    assert "Tag name cannot be empty" in result.stdout
