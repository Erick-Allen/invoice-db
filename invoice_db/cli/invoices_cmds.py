import typer, sqlite3
from datetime import date
from typing import Optional

from invoice_db.db import customers as customers_db
from invoice_db.db import invoices as invoices_db
from invoice_db.db import connection
from . import common, render_customers, render_invoices, validators, require

invoices_app = typer.Typer(help="Invoice commands.")

@invoices_app.command("create", help="Create an invoice for a customer.")
def create_invoice(
    customer_id: int = typer.Option(..., "-c", "--customer-id", help="The customer to assign this invoice to."),
    total: float = typer.Option(..., "-t", "--total", help="Invoice total amount."),
    date_issued: Optional[str] = typer.Option(None, "--date-issued", help="Date invoice was issued."),
    date_due: Optional[str] = typer.Option(None, "--date-due", help="Date invoice is due."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with common.get_connection(db_path) as (connect, cursor):
        try:
            require.require_customer(cursor, customer_id)

            invoice_id = invoices_db.add_invoice_to_customer(
                cursor, 
                customer_id=customer_id, 
                total=total,
                date_issued=date_issued, 
                date_due=date_due
                )
            
        except ValueError as ve:
            common.console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            common.db_error(e)

    common.console.print(f"Created invoice (id={invoice_id}) for customer_id={customer_id}", style="success")


@invoices_app.command("list", help="List all invoices and their respective customer.")
def list_invoices(
    customer_id: Optional[int] = typer.Option(None, "-c", "--customer-id", help="Filter by customer ID."),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by: draft | sent | paid | void"),
    min_total: Optional[int] = typer.Option(None, "--min-total", help="Minimum invoice total."),
    max_total: Optional[int] = typer.Option(None, "--max-total", help="Maximum invoice total."),
    limit: int = typer.Option(100, "-l", "--limit", min=1, help="Max invoices to return."),
    offset: int = typer.Option(0, "-o", "--offset", min=0, help="Invoices to skip."),
    sort_by: str = typer.Option("created_at", "--sort-by", help="Sort by: id | date_issued | total | status"),
    desc: bool = typer.Option(True, "--desc/--asc", help="Sort direction."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")):
    
    with common.get_connection(db_path) as (connect, cursor):
        try:
            invoices = invoices_db.list_invoices(
                cursor=cursor,
                customer_id=customer_id,
                status=status,
                min_total=min_total,
                max_total=max_total,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                desc=desc,
            )
        except ValueError as ve:
            common.console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            common.db_error(e)

        if not invoices:
            render_invoices.no_invoices_found()
            return
        
        render_invoices.print_invoices_table(invoices)

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
    customer_id: Optional[int] = typer.Option(None, "-c", "--customer-id", help="Filter by customer ID."),
    status: Optional[str] = typer.Option(None, "-s", "--status", help="Filter by: draft | sent | paid | void"),
    min_total: Optional[int] = typer.Option(None, "--min-total", help="Minimum invoice total."),
    max_total: Optional[int] = typer.Option(None, "--max-total", help="Maximum invoice total."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    customer = None
    count = 0
    
    with common.get_connection(db_path) as (connect, cursor):
        try:
            if customer_id is not None:
                customer = customers_db.get_customer_by_id(cursor, customer_id=customer_id)

            count = invoices_db.count_invoices(
                cursor=cursor,
                customer_id=customer_id,
                status=status,
                min_total=min_total,
                max_total=max_total,
            )
            
        except ValueError as ve:
            common.console.print(f"{ve}", style="error")
        except sqlite3.Error as e:
            common.db_error(e)

    label = render_invoices.build_count_label(customer, status, min_total, max_total)
    render_invoices.print_invoice_count(count, label)

@invoices_app.command("overdue", help="Display invoices with overdue status.")
def overdue_invoices(
    customer_id: Optional[int] = typer.Option(None, "-c", "--customer-id", help="Filter by customer ID."),
    days_overdue: Optional[int] = typer.Option(None, "--days-overdue", help="Days overdue by."),
    min_total: Optional[int] = typer.Option(None, "--min-total", help="Minimum invoice total."),
    max_total: Optional[int] = typer.Option(None, "--max-total", help="Maximum invoice totaltotal."),
    limit: int = typer.Option(100, "-l", "--limit", min=1, help="Max invoices to return."),
    offset: int = typer.Option(0, "-o", "--offset", min=0, help="Invoices to skip."),
    sort_by: str = typer.Option("date_issued", "--sort-by", help="Sort by: id | date_issued | total | days_overdue"),
    desc: bool = typer.Option(True, "--desc/--asc", help="Sort direction."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with common.get_connection(db_path) as (connect, cursor):
        try:
            invoices = invoices_db.list_overdue_invoices(
                cursor=cursor,
                customer_id=customer_id,
                days_overdue=days_overdue,
                min_total=min_total,
                max_total=max_total,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                desc=desc,
            )

        except sqlite3.Error as e:
            common.db_error(e)
    
    if not invoices:
        render_invoices.no_invoices_found()
        return
    
    render_invoices.print_invoices_table_overdue(invoices)

    
        
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
            validators.validate_invoice_changes(invoice, new_date_due, new_date_issued, new_total, new_customer)
            
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

    fields = render_invoices.build_changed_fields_label(new_customer, new_date_issued, new_date_due, new_total)
    if updated_invoice:
        render_invoices.print_invoice_update(updated_invoice['id'], fields)
        render_invoices.print_invoice_table(updated_invoice)
    else:
        common.console.print("Updated invoice, but failed to reload record.", style="error")
        raise typer.Exit(code=1)
    
@invoices_app.command("set-status", help="Update the status of an invoice.")
def set_status(
    invoice_id: int = typer.Option(..., "-i", "--id", help="Invoice ID."),
    status: str = typer.Option(..., "-s", "--status", help="draft | sent | paid | void"),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLITE DB."),
):
    with common.get_connection(db_path) as (connect, cursor):
        try:
            updated = invoices_db.set_invoice_status(cursor, invoice_id, status)
            updated_invoice = invoices_db.get_invoice_by_id(cursor, invoice_id=invoice_id)
        except ValueError as ve:
            common.console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            common.db_error(e)

        if not updated:
            render_invoices.invoice_not_found(invoice_id)
            raise typer.Exit(code=1)
        
        common.console.print(f"Updated invoice (id={invoice_id}, status -> {status.lower()})", style="success")
        render_invoices.print_invoice_table(updated_invoice)

        
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
    
    common.console.print(f"Deleted invoice (id={invoice_id})", style="success")