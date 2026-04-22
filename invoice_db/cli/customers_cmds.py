import typer, sqlite3
from typing import Optional

from invoice_db.db import customers as customers_db
from invoice_db.db import connection
from . import common, render_customers, validators, require

customers_app = typer.Typer(help="customer commands.")

@customers_app.command("create", help="Create and add a new customer to the database.")
def create_customer(
    customer_name: str = typer.Option(..., "-n", "--name", help="Name of the customer."),
    email: str = typer.Option(..., "-e", "--email", help="Email of the customer."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with common.get_connection(db_path) as (connect, cursor):
        try:
            customer_id = customers_db.create_customer(cursor, customer_name, email)

            customer = customers_db.get_customer_by_id(cursor, customer_id)

        except ValueError as ve:
            common.console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:  
            common.db_error(e)
        
    common.console.print(f"Created customer: {customer['name']} <{customer['email']}> (id={customer['id']})", style="success")
        
@customers_app.command("get", help="Get customer by id or email.")
def get_customer(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the customer"),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the customer"),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB")

):
    if id is None and email_selector is None:
        common.console.print("Please provide either --id or --email", style="warning")
        raise typer.Exit(code=1)
    
    if id and email_selector:
        common.console.print("Please provide only one of --id or --email (not both)", style="warning")
        raise typer.Exit(code=1)
    
    with common.get_connection(db_path) as (connect, cursor):
        try: 
            if id:
                customer = customers_db.get_customer_by_id(cursor, id)
            else:
                customer = customers_db.get_customer_by_email(cursor, email_selector)

        except sqlite3.Error as e:
            common.db_error(e)
        
    if customer:
        render_customers.print_customer_summary(customer)
    else:
        render_customers.customer_not_found(id)

@customers_app.command("list", help="List all customers in the database.")
def list_customers(
        db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with common.get_connection(db_path) as (connect, cursor):
        try:
            customers = customers_db.get_customers(cursor)
            
        except sqlite3.Error as e:
            common.db_error(e)

    if customers:
        render_customers.print_customers_table(customers)
    else:
        common.console.print("No customers found", style="warning")
        

@customers_app.command("update", help="Update the customer's name or email.")
def update_customer(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the customer."),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the customer."),
    new_name: Optional[str] = typer.Option(None, "--name", help="Name to update customer with."),
    new_email: Optional[str] = typer.Option(None,  "--new-email", help="Email to update customer with."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    updated_customer = None

    if id is None and email_selector is None:
        common.console.print("Please provide either --id or --email to select a customer", style="warning")
        raise typer.Exit(code=1)
    if id is not None and email_selector is not None:
        common.console.print("Please provide only one of --id or --email (not both)", style="warning")
        raise typer.Exit(code=1)
    if new_name is None and new_email is None:
        common.console.print("Please provide --name and/or --new-email", style="warning")
        raise typer.Exit(code=1)
    
    with common.get_connection(db_path) as (connect, cursor):
        try:
            customer = require.require_customer(cursor, id, email_selector)
            
            validators.validate_customer_changes(customer, new_name, new_email)
            
            updated = customers_db.update_customer(cursor, customer['id'], new_name, new_email)
                
            updated_customer = customers_db.get_customer_by_id(cursor, customer['id'])

        except ValueError as ve:
            common.console.print(f"{ve}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            common.db_error(e)

    if updated_customer:
        render_customers.print_customer_summary(updated_customer)
    else:
        common.console.print("Updated customer, but failed to reload record.", style="error")
        raise typer.Exit(code=1)
    


@customers_app.command("delete", help="Deletes a single customer in the database.")
def delete_customer_by_id(
    customer_id: int = typer.Option(..., "-i", "--id", help="ID of the customer."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with common.get_connection(db_path) as (connect, cursor):
        try:
            deleted = customers_db.delete_customer(cursor=cursor, customer_id=customer_id)

        except sqlite3.Error as e:  
            common.db_error(e)

        if not deleted:
            common.console.print(f"Customer not found with id={customer_id}", style="error")
            raise typer.Exit(code=1)

        common.console.print(f"Deleted customer (id={customer_id})", style="success")
