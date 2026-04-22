import typer
from invoice_db.db import utils
from . import common

def validate_customer_changes(customer: dict, new_name: str, new_email: str) -> None:
    no_name_change = new_name is None or new_name == customer['name']
    no_email_change = new_email is None or new_email == customer['email']
    if no_name_change and no_email_change:
        common.console.print("No changes were applied", style="warning")
        raise typer.Exit(code=1)
    
def validate_invoice_changes(invoice: dict, new_date_due: str, new_date_issued: str, new_total: int, new_customer: int) -> None:
    no_new_date_issued = new_date_issued is None or utils.to_iso(new_date_issued) == invoice['date_issued']
    no_new_date_due = new_date_due is None or utils.to_iso(new_date_due) == invoice['date_due']
    no_new_total = new_total is None or utils.to_cents(new_total) == invoice['total']
    no_new_customer = new_customer is None or new_customer == invoice['customer_id']

    if no_new_date_issued and no_new_date_due and no_new_total and no_new_customer:
        common.console.print("No changes were applied", style="warning")
        raise typer.Exit(code=1)
    
