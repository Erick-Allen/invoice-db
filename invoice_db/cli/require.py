import typer
from invoice_db.db import customers as customers_db
from invoice_db.db import invoices as invoices_db
from . import render_customers, render_invoices

def require_customer(cursor, customer_id: int | None = None, email: str | None = None) -> dict:
    if customer_id is None and email is None:
        raise ValueError("require_customer needs customer_id or email")
    elif customer_id is not None:
        customer = customers_db.get_customer_by_id(cursor, customer_id)
    elif email is not None:
        customer = customers_db.get_customer_by_email(cursor, email)

    if customer:
        return customer
    else:
        render_customers.customer_not_found(customer_id, email)
        raise typer.Exit(code=1)
    
def require_invoice(cursor, invoice_id: int) -> dict:
    invoice = invoices_db.get_invoice_by_id(cursor=cursor, invoice_id=invoice_id)
    if invoice:
        return invoice
    else:
        render_invoices.invoice_not_found(invoice_id)
        raise typer.Exit(code=1)
    