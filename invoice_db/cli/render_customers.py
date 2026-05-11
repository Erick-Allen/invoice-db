from . import ui
from rich.table import Table

def customer_not_found(customer_id: int | None = None, email: str | None = None) -> None:
    if customer_id is not None:
        ui.console.print(f"Customer not found (id={customer_id})", style="warning")
    elif email is not None:
        ui.console.print(f"Customer not found (email={email})", style="warning")
    else:
        ui.console.print("Customer not found", style="warning")    

def no_customers_found() -> None:
    ui.console.print("No customers found", style="warning")

def print_customer_summary(customer: dict) -> None:
    ui.console.print("[title]ID   NAME     EMAIL[/title]")
    ui.console.print(
        f"{customer['id']:<4} "
        f"{customer['name']:<8} "
        f"{customer['email']}\n"
    )

def print_customers_table(customers: dict) -> None:
    table = Table(title="customers")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Email")

    for u in customers:
        table.add_row(str(u['id']), u['name'], u['email'])
    ui.console.print(table)
