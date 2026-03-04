import typer, sqlite3
from datetime import date
from typing import Optional

from invoice_db.db import customers as customers_db
from invoice_db.db import invoices as invoices_db
from invoice_db.db import connection, reports
from . import common, render_customers, render_invoices, validators, require

invoices_app = typer.Typer(help="Invoice commands.")

@invoices_app.command("create", help="Create an invoice for a customer.")
def create_invoice(
    customer_id: int = typer.Option(..., "-i", "--id", help="The customer to assign this invoice to."),
    total: float = typer.Option(..., "-t", "--total", help="Invoice total amount."),
    date_issued: Optional[str] = typer.Option(None, "--date-issued", help="Date invoice was issued."),
    date_due: Optional[str] = typer.Option(None, "--date-due", help="Date invoice is due."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with common.get_connection(db_path) as (connect, cursor):
        try:
            require.require_customer(cursor, customer_id)
            
            if date_issued is None:
                date_issued = date.today().isoformat()

            invoice_id = invoices_db.add_invoice_to_customer(
                cursor, 
                customer_id=customer_id, 
                total=total,
                date_issued=date_issued, 
                date_due=date_due
                )
            
        except sqlite3.Error as e:
            common.db_error(e)

    common.console.print(f"Invoice {invoice_id} created for customer {customer_id} (total: {total})", style="success")


@invoices_app.command("list", help="List all invoices and their respective customer.")
def list_invoices(
    customer_id: Optional[int] = typer.Option(None, "-u", "--customer-id", help="Filter by customer ID."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")):
    
    customer = None
    customers = None
    customer_invoices = None
    customers_with_invoices: list[tuple[dict, list]] = []

    with common.get_connection(db_path) as (connect, cursor):
        try:
            if customer_id is not None:
                customer = customers_db.get_customer_by_id(cursor=cursor, customer_id=customer_id)
                customer_invoices = invoices_db.get_invoices_by_customer_id(cursor=cursor, customer_id=customer_id)
            else:
                customers = reports.get_customers(cursor)
                for u in customers:
                    invs = invoices_db.get_invoices_by_customer_id(cursor, u['id'])
                    customers_with_invoices.append((u, invs))
        except sqlite3.Error as e:
            common.db_error(e)

    if customer_id is not None:
        if customer:
            render_invoices.display_customer_and_invoices(customer, customer_invoices)
        else:
            render_customers.customer_not_found(customer_id)
        return
    
    if customers:
        for customer, invs in (customers_with_invoices):
            render_invoices.display_customer_and_invoices(customer, invs)
    else:
        render_customers.no_customers_found()
            

@invoices_app.command("get", help="Get invoice by its ID.")
def get_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="ID of invoice to get."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with common.get_connection(db_path) as (connect, cursor):
        try:
            invoice = invoices_db.get_invoice_by_id(cursor, invoice_id)

        except sqlite3.Error as e:
            common.db_error(e)

        if invoice:
            render_invoices.print_invoice_table(invoice)
        else:
            render_invoices.invoice_not_found(invoice_id)
            
        
@invoices_app.command("count", help="Count number of invoices.")
def count_invoices(
    customer_id: Optional[int] = typer.Option(None, "-u", "--customer-id", help="Filter by customer ID."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    customer = None
    count = 0
    
    with common.get_connection(db_path) as (_, cursor):
        try:
            if customer_id is not None:
                customer = customers_db.get_customer_by_id(cursor, customer_id)
                if customer:
                    count = invoices_db.count_invoices_by_customer(cursor=cursor, customer_id=customer_id)
            else:
                count = invoices_db.count_invoices(cursor)      

        except sqlite3.Error as e:
            common.db_error(e)

    if customer_id is not None and customer is None:
        render_customers.customer_not_found(customer_id)
        return
    render_invoices.print_invoice_count(count, customer)
    
        
@invoices_app.command("update", help="Update an invoice's: date_issued, date_due, total, or customer.")
def update_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="Invoice id to select."),
    new_date_issued: Optional[str] = typer.Option(None, "--date-issued", help="Date to update date issued."),
    new_date_due: Optional[str] = typer.Option(None, "--date-due", help="Date to update due date."),
    new_total: Optional[float] = typer.Option(None, "--total", help="New total for the invoice."),
    new_customer: Optional[int] = typer.Option(None, "--customer", help="customer to append the invoice to."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    updated_invoice = None

    if (
        new_date_issued is None 
        and new_date_due is None 
        and new_total is None 
        and new_customer is None
    ):
        common.console.print("Please enter one value to update the invoice with (refer to --help)", style="warning")
        raise typer.Exit(code=1)

    with common.get_connection(db_path) as (connect, cursor):
        try:
            invoice = require.require_invoice(cursor, invoice_id)
            validators.ensure_invoice_has_changes(invoice, new_date_due, new_date_issued, new_total, new_customer)
            
            updated = invoices_db.update_invoice(
                cursor=cursor,
                invoice_id=invoice_id,
                date_issued=new_date_issued,
                date_due=new_date_due,
                total=new_total,
                customer_id=new_customer
                )
            
            if not updated:
                 common.console.print("No changes were applied", style="warning")
                 raise typer.Exit(code=1)
            
            updated_invoice = invoices_db.get_invoice_by_id(cursor, invoice_id=invoice_id)
            
        except ValueError as ve:
            common.console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            common.db_error(e)

    if updated_invoice:
        common.console.print("Update Successful", style="success")
        render_invoices.print_invoice_table(updated_invoice)
    else:
        common.console.print("Updated invoice, but failed to reload record.", style="error")
        raise typer.Exit(code=1)


        
@invoices_app.command("delete", help="Deletes a single invoice from the database.")
def delete_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="ID of the invoice."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with common.get_connection(db_path) as (connect, cursor):
        try:
            deleted = invoices_db.delete_invoice(cursor=cursor, invoice_id=invoice_id)

        except sqlite3.Error as e:
            common.db_error(e)

        if not deleted:
            render_invoices.invoice_not_found(invoice_id)
            raise typer.Exit(code=1)
    
    common.console.print(f"Deleted invoice {invoice_id}", style="success")