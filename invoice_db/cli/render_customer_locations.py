from rich.table import Table

from . import ui


def no_customer_locations_found() -> None:
    ui.console.print("No customer locations found", style="warning")


def print_customer_location(location: dict) -> None:
    table = Table(title=f"Customer Location (id={location['id']})")
    table.add_column("Label")
    table.add_column("Address")
    table.add_column("Status")
    table.add_column("Primary")

    address = _format_address(location)
    table.add_row(
        location["label"],
        address,
        "active" if location["is_active"] else "inactive",
        "yes" if location["is_primary"] else "no",
    )
    ui.console.print(table)


def print_customer_locations_table(locations: list[dict]) -> None:
    table = Table(title="Customer Locations")
    table.add_column("ID", justify="right")
    table.add_column("Label")
    table.add_column("Address")
    table.add_column("Status")
    table.add_column("Primary")

    for location in locations:
        table.add_row(
            str(location["id"]),
            location["label"],
            _format_address(location),
            "active" if location["is_active"] else "inactive",
            "yes" if location["is_primary"] else "no",
        )

    ui.console.print(table)


def _format_address(location: dict) -> str:
    line2 = f", {location['address_line2']}" if location["address_line2"] else ""
    return (
        f"{location['address_line1']}{line2}, "
        f"{location['city']}, {location['state']} {location['postal_code']}, "
        f"{location['country']}"
    )
