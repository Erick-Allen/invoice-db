from rich.table import Table

from . import ui


def no_product_categories_found() -> None:
    ui.console.print("No product categories found", style="warning")


def print_product_category_table(category: dict) -> None:
    table = Table(title=f"Product Category (id={category['id']})")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Active", justify="center")
    table.add_column("Description")

    table.add_row(
        str(category["id"]),
        category["name"],
        "yes" if category["is_active"] else "no",
        category["description"] or "[muted]-[/muted]",
    )
    ui.console.print(table)


def print_product_categories_table(categories: list[dict]) -> None:
    table = Table(title="[title]Product Categories[/title]")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Active", justify="center")
    table.add_column("Description")

    for category in categories:
        table.add_row(
            str(category["id"]),
            category["name"],
            "yes" if category["is_active"] else "no",
            category["description"] or "[muted]-[/muted]",
        )

    ui.console.print(table)
