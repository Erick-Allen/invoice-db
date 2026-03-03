import typer, sqlite3 
from .db import schema, reports, utils, connection
from .db import customers as customers_db
from .db import invoices as invoices_db
from datetime import date
from typing import Optional
from contextlib import contextmanager
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.theme import Theme

THEME = Theme({
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "danger": "bold red",
    "accent": "magenta",
    "highlight": "cyan",
    "muted": "dim",
    "title": "bold",
})

console = Console(highlight=False, theme=THEME)

#HELPERS

###CUSTOMERS
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
        customer_not_found(customer_id, email)
        raise typer.Exit(code=1)
    
def customer_not_found(customer_id: int | None = None, email: str | None = None) -> None:
    if customer_id is not None:
        console.print(f"customer not found (id={customer_id})", style="warning")
    elif email is not None:
        console.print(f"customer not found (email={email})", style="warning")
    else:
        console.print("customer not found", style="warning")    
    
def no_customers_found() -> None:
    console.print("No customers found", style="warning")

def print_customer_summary(customer: dict) -> None:
    console.print("[title]ID   NAME     EMAIL[/title]")
    console.print(
        f"{customer['id']:<4} "
        f"{customer['name']:<8} "
        f"{customer['email']}\n"
    )

def print_customers_table(customers) -> None:
    table = Table(title="customers")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Email")

    for u in customers:
        table.add_row(str(u['id']), u['name'], u['email'])
    console.print(table)

def ensure_customer_has_changes(customer, new_name, new_email) -> None:
    no_name_change = new_name is None or new_name == customer['name']
    no_email_change = new_email is None or new_email == customer['email']
    if no_name_change and no_email_change:
        console.print("No changes were applied", style="warning")
        raise typer.Exit(code=1)

def delete_customer_record(cursor, customer_id) -> None:
    deleted = customers_db.delete_customer(cursor, customer_id)
    if not deleted:
        console.print(f"Nothing deleted for ID {customer_id}", style="error")
        raise typer.Exit(code=1)

###INVOICES    
def require_invoice(cursor, invoice_id: int) -> dict:
    invoice = invoices_db.get_invoice_by_id(cursor=cursor, invoice_id=invoice_id)
    if invoice:
        return invoice
    else:
        invoice_not_found(invoice_id)
        raise typer.Exit(code=1)

def invoice_not_found(invoice_id: int | None = None) -> None:
    if invoice_id is not None:
        console.print(f"Invoice not found (id={invoice_id})", style ="warning")
    else:
        console.print("Invoice not found", style="warning")

def no_invoices_found() -> None:
    console.print("No invoices found", style="warning")

def print_invoice_table(invoice) -> None:
    table = Table(title=f"Invoice (id={invoice['invoice_id']})")
    table.add_column("ID", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Issued", justify="center")
    table.add_column("Due", justify="center")

    due = utils.fmt_optional(invoice["date_due"])
    if due == "-":
            due = "[muted]-[/muted]"
    table.add_row(str(invoice['invoice_id']), str(utils.fmt_dollars(invoice['total'])), str(invoice['date_issued']), due)
    console.print(table)

def print_invoices_table(customer, invoices) -> None:
    table = Table(title=f"[title]{customer} Invoices[/title]")
    table.add_column("ID", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Issued", justify="center", style="muted")
    table.add_column("Due", justify="center")

    for i in invoices:
        due = utils.fmt_optional(i["date_due"])
        if due == "-":
            due = "[muted]-[/muted]"
        table.add_row(str(i['invoice_id']), str(utils.fmt_dollars(i['total'])), str(i['date_issued']), due)
    console.print(table)

def print_invoice_count(count, customer) -> None:
    if customer:
        console.print(f"Invoices [accent]for[/accent] {customer['name']}: [highlight]{count}[/highlight]")
    else:
        console.print(f"Total number of invoices: [highlight]{count}[/highlight]")

def display_customer_and_invoices(customer, invoices) -> None:
    print_customer_summary(customer)
    if invoices:
        print_invoices_table(customer['name'], invoices)
    else:
        no_invoices_found()
        print()

def delete_invoice_record(cursor, invoice_id) -> None:
    deleted = invoices_db.delete_invoice(cursor=cursor, invoice_id=invoice_id)
    if not deleted:
        console.print(f"Nothing deleted for invoice {invoice_id}", style="error")
        raise typer.Exit(code=1)

###ERRORS
def db_error(e: Exception) -> None:
    console.print(f"Database error: {e}", style="error")
    raise typer.Exit(code=1)

def ensure_invoice_has_changes(invoice, new_date_due, new_date_issued, new_total, new_customer) -> None:
    no_new_date_issued = new_date_issued is None or utils.to_iso(new_date_issued) == invoice['date_issued']
    no_new_date_due = new_date_due is None or utils.to_iso(new_date_due) == invoice['date_due']
    no_new_total = new_total is None or utils.to_cents(new_total) == invoice['total']
    no_new_customer = new_customer is None or new_customer == invoice['customer_id']

    if no_new_date_issued and no_new_date_due and no_new_total and no_new_customer:
        console.print("No changes were applied", style="warning")
        raise typer.Exit(code=1)

#CLI APP
__version__ = "0.5.1"
app = typer.Typer(help="Command Line Interface for the customer_Invoice_Database.\n\n"
                  "Use '--help' after any command for more details.\n\n"
                  "Example: invoicedb --help")
db = typer.Typer(help="Database commands.")
customers = typer.Typer(help="customer commands.")
invoices = typer.Typer(help="Invoice commands.")
app.add_typer(db, name="db")
app.add_typer(customers, name="customers")
app.add_typer(invoices, name="invoices")

@app.callback(invoke_without_command=True)
def main(
        ctx: typer.Context,
        version: bool = typer.Option(None, "--version", "-v", 
        help="Show the CLI version and exit.", is_eager=True
    )
):
    if version:
        console.print(f"customer_invoice_db CLI version [highlight]{__version__}[/highlight]")
        raise typer.Exit()
        
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()
    
    
    
@contextmanager
def get_connection(db_path=connection.DB_PATH):
    connect = sqlite3.connect(db_path)
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    try:
        yield connect, cursor
    finally:
        connect.close()

# ----- DATABASE COMMANDS ------ 
@db.command("init", help="Initialize a new database with all tables and schema.")
def init_db_command(
        db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        schema.create_customer_schema(cursor)
        schema.create_invoice_schema(cursor)
        connect.commit()
    console.print("Initialized database", style="success")

@db.command("drop", help="Drop all database tables (does not delete file).")
def drop_db_command(
        db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        cursor.execute("DROP TABLE IF EXISTS invoices;")
        cursor.execute("DROP TABLE IF EXISTS customers;")
        connect.commit()
    console.print(f"Dropped all tables from {db_path}", style="success")

@db.command("delete", help="Permanently delete the database file from disk.")
def delete_db_file(
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    import os  # Used only for safe local file operations (e.g., deleting DB)
    if not os.path.exists(db_path):
        console.print(f"No database found at {db_path}", style="error")
        raise typer.Exit(code=1)
    
    confirm = Confirm.ask(f"[danger]Are you sure you want to permanently delete '{db_path}'?[/danger]")
    if not confirm:
        console.print(f"Deletion cancelled", style="warning")
        raise typer.Exit(code=0)
    
    os.remove(db_path)
    console.print(f"Database file '{db_path}' deleted successfully", style="success")

# ----- customer COMMANDS ------ 
@customers.command("create", help="Create and add a new customer to the database.")
def create_customer(
    customer_name: str = typer.Option(..., "-n", "--name", help="Name of the customer."),
    email: str = typer.Option(..., "-e", "--email", help="Email of the customer."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            customer_id = customers_db.create_customer(cursor, customer_name, email)
            connect.commit()

            customer = customers_db.get_customer_by_id(cursor, customer_id)

        except ValueError as ve:
            console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:  
            db_error(e)
        
    console.print(f"Created customer {customer['name']} <{customer['email']}> (id={customer['id']})", style="success")
        
@customers.command("get", help="Get customer by id or email.")
def get_customer(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the customer"),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the customer"),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB")

):
    if id is None and email_selector is None:
        console.print("Please provide either --id or --email", style="warning")
        raise typer.Exit(code=1)
    
    if id and email_selector:
        console.print("Please provide only one of --id or --email (not both)", style="warning")
        raise typer.Exit(code=1)
    
    with get_connection(db_path) as (connect, cursor):
        try: 
            if id:
                customer = customers_db.get_customer_by_id(cursor, id)
            else:
                customer = customers_db.get_customer_by_email(cursor, email_selector)

        except sqlite3.Error as e:
            db_error(e)
        
    if customer:
        print_customer_summary(customer)
    else:
        customer_not_found(id)

@customers.command("list", help="List all customers in the database.")
def list_customers(
        db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            customers = reports.get_customers(cursor)
            
        except sqlite3.Error as e:
            db_error(e)

    if customers:
        print_customers_table(customers)
    else:
        console.print("No customers found", style="warning")
        

@customers.command("update", help="Update the customer's name or email.")
def update_customer(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the customer."),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the customer."),
    new_name: Optional[str] = typer.Option(None, "--name", help="Name to update customer with."),
    new_email: Optional[str] = typer.Option(None,  "--new-email", help="Email to update customer with."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    updated_customer = None

    if id is None and email_selector is None:
        console.print("Please provide either --id or --email to select a customer", style="warning")
        raise typer.Exit(code=1)
    if id is not None and email_selector is not None:
        console.print("Please provide only one of --id or --email (not both)", style="warning")
        raise typer.Exit(code=1)
    if new_name is None and new_email is None:
        console.print("Please provide --name and/or --new-email", style="warning")
        raise typer.Exit(code=1)
    
    with get_connection(db_path) as (connect, cursor):
        try:
            customer = require_customer(cursor, id, email_selector)
            
            ensure_customer_has_changes(customer, new_name, new_email)
            
            updated = customers_db.update_customer(cursor, customer['id'], new_name, new_email)
                
            connect.commit()
            updated_customer = customers_db.get_customer_by_id(cursor, customer['id'])

        except ValueError as ve:
            console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            db_error(e)

    if updated_customer:
        print_customer_summary(updated_customer)
    else:
        console.print("Updated customer, but failed to reload record.", style="error")
        raise typer.Exit(code=1)
    


@customers.command("delete", help="Deletes a single customer in the database.")
def delete_customer_by_id(
    customer_id: int = typer.Option(..., "-i", "--id", help="ID of the customer."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            require_customer(cursor, customer_id)

            delete_customer_record(cursor, customer_id)

            connect.commit()
            console.print(f"Deleted customer: (id={customer_id})", style="success")

        except sqlite3.Error as e:  
            db_error(e)
        
    

# ----- INVOICES COMMANDS ------ 
@invoices.command("create", help="Create an invoice for a customer.")
def create_invoice(
    customer_id: int = typer.Option(..., "-i", "--id", help="The customer to assign this invoice to."),
    total: float = typer.Option(..., "-t", "--total", help="Invoice total amount."),
    date_issued: Optional[str] = typer.Option(None, "--date-issued", help="Date invoice was issued."),
    date_due: Optional[str] = typer.Option(None, "--date-due", help="Date invoice is due."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            require_customer(cursor, customer_id)
            
            if date_issued is None:
                date_issued = date.today().isoformat()

            invoice_id = invoices_db.add_invoice_to_customer(
                cursor, 
                customer_id=customer_id, 
                total=total,
                date_issued=date_issued, 
                date_due=date_due
                )
            connect.commit()

        except sqlite3.Error as e:
            db_error(e)

    console.print(f"Invoice {invoice_id} created for customer {customer_id} (total: {total})", style="success")


@invoices.command("list", help="List all invoices and their respective customer.")
def list_invoices(
    customer_id: Optional[int] = typer.Option(None, "-u", "--customer-id", help="Filter by customer ID."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")):
    
    customer = None
    customers = None
    customer_invoices = None
    customers_with_invoices: list[tuple[dict, list]] = []

    with get_connection(db_path) as (connect, cursor):
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
            db_error(e)

    if customer_id is not None:
        if customer:
            display_customer_and_invoices(customer, customer_invoices)
        else:
            customer_not_found(customer_id)
        return
    
    if customers:
        for customer, invs in (customers_with_invoices):
            display_customer_and_invoices(customer, invs)
    else:
        no_customers_found()
            

@invoices.command("get", help="Get invoice by its ID.")
def get_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="ID of invoice to get."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            invoice = invoices_db.get_invoice_by_id(cursor, invoice_id)

        except sqlite3.Error as e:
            db_error(e)

        if invoice:
            print_invoice_table(invoice)
        else:
            invoice_not_found(invoice_id)
            
        
@invoices.command("count", help="Count number of invoices.")
def count_invoices(
    customer_id: Optional[int] = typer.Option(None, "-u", "--customer-id", help="Filter by customer ID."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    customer = None
    count = 0
    
    with get_connection(db_path) as (_, cursor):
        try:
            if customer_id is not None:
                customer = customers_db.get_customer_by_id(cursor, customer_id)
                if customer:
                    count = invoices_db.count_invoices_by_customer(cursor=cursor, customer_id=customer_id)
            else:
                count = invoices_db.count_invoices(cursor)      

        except sqlite3.Error as e:
            db_error(e)

    if customer_id is not None and customer is None:
        customer_not_found(customer_id)
        return
    print_invoice_count(count, customer)
    
        
@invoices.command("update", help="Update an invoice's: date_issued, date_due, total, or customer.")
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
        console.print("Please enter one value to update the invoice with (refer to --help)", style="warning")
        raise typer.Exit(code=1)

    with get_connection(db_path) as (connect, cursor):
        try:
            invoice = require_invoice(cursor, invoice_id)
            ensure_invoice_has_changes(invoice, new_date_due, new_date_issued, new_total, new_customer)
            
            updated = invoices_db.update_invoice(
                cursor=cursor,
                invoice_id=invoice_id,
                date_issued=new_date_issued,
                date_due=new_date_due,
                total=new_total,
                customer_id=new_customer
                )
            
            if not updated:
                 console.print("No changes were applied", style="warning")
                 raise typer.Exit(code=1)
            
            connect.commit()
            updated_invoice = invoices_db.get_invoice_by_id(cursor, invoice_id=invoice_id)
            
        except ValueError as ve:
            console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            db_error(e)

    if updated_invoice:
        console.print("Update Successful", style="success")
        print_invoice_table(updated_invoice)
    else:
        console.print("Updated invoice, but failed to reload record.", style="error")
        raise typer.Exit(code=1)


        
@invoices.command("delete", help="Deletes a single invoice from the database.")
def delete_invoice(
    invoice_id: int = typer.Option(..., "-i", "--id", help="ID of the invoice."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with get_connection(db_path) as (connect, cursor):
        try:
            require_invoice(cursor, invoice_id)
            
            delete_invoice_record(cursor, invoice_id)
            connect.commit()
            
        except sqlite3.Error as e:
            db_error(e)

    console.print(f"Deleted invoice {invoice_id}", style="success")