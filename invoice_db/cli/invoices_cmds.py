import typer, sqlite3
from typing import Optional

from invoice_db.db import connection
from invoice_db.services import invoices as invoices_services
from invoice_db.services import invoice_items as invoice_item_services
from invoice_db.services import exceptions as service_exceptions
from . import render_invoices, ui
from ..utils import to_cents

invoices_app = typer.Typer(help="Invoice commands.")

@invoices_app.command("create", help="Create an invoice for a customer.")
def create_invoice(
    customer_id: int = typer.Option(..., "-c", "--customer-id", help="The customer to assign this invoice to."),
    date_issued: Optional[str] = typer.Option(None, "--date-issued", help="Date invoice was issued."),
    date_due: Optional[str] = typer.Option(None, "--date-due", help="Date invoice is due."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            invoice = invoices_services.create_invoice(
                cursor,
                customer_id=customer_id,
                date_issued=date_issued,
                date_due=date_due,
            )
            
        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.ServiceError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Created invoice (id={invoice['id']}) for customer_id={customer_id}", style="success")


@invoices_app.command("list", help="List all invoices and their respective customer.")
def list_invoices(
    customer_id: Optional[int] = typer.Option(None, "-c", "--customer-id", help="Filter by customer ID."),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by: draft | sent | paid | void"),
    min_total: Optional[float] = typer.Option(None, "--min-total", help="Minimum invoice total."),
    max_total: Optional[float] = typer.Option(None, "--max-total", help="Maximum invoice total."),
    include_items: bool = typer.Option(False, "--include-items", help="Include line items for each invoice."),
    limit: int = typer.Option(100, "-l", "--limit", min=1, help="Max invoices to return."),
    offset: int = typer.Option(0, "-o", "--offset", min=0, help="Invoices to skip."),
    sort_by: str = typer.Option("created_at", "--sort-by", help="Sort by: id | date_issued | total | status"),
    desc: bool = typer.Option(True, "--desc/--asc", help="Sort direction."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")):

    with connection.db_session(db_path) as (connect, cursor):
        try:
            invoices = invoices_services.list_invoices(
                cursor=cursor,
                customer_id=customer_id,
                status=status,
                min_total=to_cents(min_total) if min_total is not None else None,
                max_total=to_cents(max_total) if max_total is not None else None,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                desc=desc,
            )
            invoice_items_by_id = {
                invoice["id"]: invoice_item_services.list_invoice_items(cursor, invoice["id"])
                for invoice in invoices
            } if include_items else {}

        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)

    if invoices:
        render_invoices.print_invoices_table(invoices)
        if include_items:
            for invoice in invoices:
                render_invoices.print_invoice_items_by_invoice(invoice["id"], invoice_items_by_id[invoice["id"]])
    else:
        render_invoices.no_invoices_found()
        
        
@invoices_app.command("get", help="Get invoice by its ID.")
def get_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="ID of invoice to get."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            invoice = invoices_services.get_invoice_by_id(cursor, invoice_id)
            invoice_items = invoice_item_services.list_invoice_items(cursor, invoice_id)

        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)

    if invoice:
        render_invoices.print_invoice_table(invoice)
        render_invoices.print_invoice_line_items(invoice_items)
    else:
        render_invoices.invoice_not_found(invoice_id)
            
        
@invoices_app.command("count", help="Count number of invoices.")
def count_invoices(
    customer_id: Optional[int] = typer.Option(None, "-c", "--customer-id", help="Filter by customer ID."),
    status: Optional[str] = typer.Option(None, "-s", "--status", help="Filter by: draft | sent | paid | void"),
    min_total: Optional[float] = typer.Option(None, "--min-total", help="Minimum invoice total."),
    max_total: Optional[float] = typer.Option(None, "--max-total", help="Maximum invoice total."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            result = invoices_services.count_invoices(
                cursor=cursor,
                customer_id=customer_id,
                status=status,
                min_total=to_cents(min_total) if min_total is not None else None,
                max_total=to_cents(max_total) if max_total is not None else None,
            )
            
        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)

    label = render_invoices.build_count_label(
        customer=result['customer'], 
        status=result['status'],
        min_total=result['min_total'],
        max_total=result['max_total']
    )    

    render_invoices.print_invoice_count(result['count'], label)


@invoices_app.command("overdue", help="Display invoices with overdue status.")
def overdue_invoices(
    customer_id: Optional[int] = typer.Option(None, "-c", "--customer-id", help="Filter by customer ID."),
    days_overdue: Optional[int] = typer.Option(None, "--days-overdue", help="Days overdue by."),
    min_total: Optional[float] = typer.Option(None, "--min-total", help="Minimum invoice total."),
    max_total: Optional[float] = typer.Option(None, "--max-total", help="Maximum invoice totaltotal."),
    limit: int = typer.Option(100, "-l", "--limit", min=1, help="Max invoices to return."),
    offset: int = typer.Option(0, "-o", "--offset", min=0, help="Invoices to skip."),
    sort_by: str = typer.Option("date_issued", "--sort-by", help="Sort by: id | date_issued | total | days_overdue"),
    desc: bool = typer.Option(True, "--desc/--asc", help="Sort direction."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            invoices = invoices_services.overdue_invoices(
                cursor=cursor,
                customer_id=customer_id,
                days_overdue=days_overdue,
                min_total=to_cents(min_total) if min_total is not None else None,
                max_total=to_cents(max_total) if max_total is not None else None,
                offset=offset,
                sort_by=sort_by,
                desc=desc,
            )

        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)
    
    if invoices:
        render_invoices.print_invoices_table_overdue(invoices)
    else:
        render_invoices.no_invoices_found()    

        
@invoices_app.command("update", help="Update an invoice's date_issued, date_due, or customer.")
def update_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="Invoice id to select."),
    new_date_issued: Optional[str] = typer.Option(None, "--date-issued", help="Date to update date issued."),
    new_date_due: Optional[str] = typer.Option(None, "--date-due", help="Date to update due date."),
    new_customer_id: Optional[int] = typer.Option(None, "--customer", help="customer to append the invoice to."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    if (
        new_date_issued is None 
        and new_date_due is None 
        and new_customer_id is None
    ):
        ui.console.print("Please enter one value to update the invoice with (refer to --help)", style="warning")
        raise typer.Exit(code=1)

    with connection.db_session(db_path) as (connect, cursor):
        try:
            updated_invoice = invoices_services.update_invoice_by_id(
                cursor=cursor,
                invoice_id=invoice_id,
                new_date_issued=new_date_issued,
                new_date_due=new_date_due,
                new_customer_id=new_customer_id
                )
            
        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.ServiceError as e:
            ui.console.print(str(e), style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)

    fields = render_invoices.build_changed_fields_label(new_customer_id, new_date_issued, new_date_due)
    render_invoices.print_invoice_update(updated_invoice['id'], fields)
    render_invoices.print_invoice_table(updated_invoice)


@invoices_app.command("set-status", help="Update the status of an invoice.")
def set_status(
    invoice_id: int = typer.Option(..., "-i", "--id", help="Invoice ID."),
    status: str = typer.Option(..., "-s", "--status", help="draft | sent | paid | void"),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLITE DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            updated_invoice = invoices_services.set_invoice_status(cursor, invoice_id, status)
        
        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.ServiceError as e:
            ui.console.print(str(e), style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)
        
    ui.console.print(f"Updated invoice (id={invoice_id}, status -> {updated_invoice['status']})", style="success")
    render_invoices.print_invoice_table(updated_invoice)

        
@invoices_app.command("delete", help="Deletes a single invoice from the database.")
def delete_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="ID of the invoice."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            invoices_services.delete_invoice(cursor=cursor, invoice_id=invoice_id)

        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)
    
    ui.console.print(f"Deleted invoice (id={invoice_id})", style="success")
