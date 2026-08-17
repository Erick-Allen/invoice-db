from rich.table import Table

from . import ui


def no_tags_found() -> None:
    ui.console.print("No tags found", style="warning")


def print_tag_table(tag: dict) -> None:
    table = Table(title=f"Tag (id={tag['id']})")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Active", justify="center")
    table.add_column("Description")

    table.add_row(
        str(tag["id"]),
        tag["name"],
        "yes" if tag["is_active"] else "no",
        tag["description"] or "[muted]-[/muted]",
    )
    ui.console.print(table)


def print_tags_table(tags: list[dict], title: str = "[title]Tags[/title]") -> None:
    table = Table(title=title)
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Active", justify="center")
    table.add_column("Description")

    for tag in tags:
        table.add_row(
            str(tag["id"]),
            tag["name"],
            "yes" if tag["is_active"] else "no",
            tag["description"] or "[muted]-[/muted]",
        )

    ui.console.print(table)
