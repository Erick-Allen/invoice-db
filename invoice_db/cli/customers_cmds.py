import typer, sqlite3
from typing import Optional

from invoice_db.db import connection
from invoice_db.services import customers as customers_services
from invoice_db.services import exceptions as service_exceptions
from . import render_customers, ui 

customers_app = typer.Typer(help="customer commands.")

@customers_app.command("create", help="Create and add a new customer to the database.")
def create_customer(
    customer_name: str = typer.Option(..., "-n", "--name", help="Name of the customer."),
    email: str = typer.Option(..., "-e", "--email", help="Email of the customer."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            customer = customers_services.create_customer(cursor, customer_name, email)

        except service_exceptions.ValidationError as e:
            ui.console.print(f"{e}", style="error")
            raise typer.Exit(code=1)
        except service_exceptions.ServiceError as e:
            ui.console.print(f"{e}", style="error")
            raise typer.Exit(code=1)        
        except sqlite3.Error as e:  
            ui.db_error(e)
        
    ui.console.print(f"Created customer: {customer['name']} <{customer['email']}> (id={customer['id']})", style="success")
        
@customers_app.command("get", help="Get customer by id or email.")
def get_customer(
    id: Optional[int] = typer.Option(None, "-i", "--id", help="ID of the customer"),
    email_selector: Optional[str] = typer.Option(None, "-e", "--email", help="Email of the customer"),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB")

):
    if id is None and email_selector is None:
        ui.console.print("Please provide either --id or --email", style="warning")
        raise typer.Exit(code=1)
    
    if id is not None and email_selector is not None:
        ui.console.print("Please provide only one of --id or --email (not both)", style="warning")
        raise typer.Exit(code=1)
    
    with connection.db_session(db_path) as (connect, cursor):
        try: 
            if id is not None:
                customer = customers_services.get_customer_by_id(cursor, id)
            else:
                customer = customers_services.get_customer_by_email(cursor, email_selector)

        except service_exceptions.ValidationError as e:
            ui.console.print(f"{e}", style="error")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)
        
    render_customers.print_customer_summary(customer)


@customers_app.command("list", help="List all customers in the database.")
def list_customers(
        db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            customers = customers_services.list_customers(cursor)
            
        except sqlite3.Error as e:
            ui.db_error(e)

    if customers:
        render_customers.print_customers_table(customers)
    else:
        render_customers.no_customers_found()
        

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
        ui.console.print("Please provide either --id or --email to select a customer", style="warning")
        raise typer.Exit(code=1)
    if id is not None and email_selector is not None:
        ui.console.print("Please provide only one of --id or --email (not both)", style="warning")
        raise typer.Exit(code=1)
    if new_name is None and new_email is None:
        ui.console.print("Please provide --name and/or --new-email", style="warning")
        raise typer.Exit(code=1)
    
    with connection.db_session(db_path) as (connect, cursor):
        try:
            if id is not None:
                updated_customer = customers_services.update_customer_by_id(
                    cursor, 
                    customer_id=id, 
                    new_name=new_name, 
                    new_email=new_email
                    )
            else:
                updated_customer = customers_services.update_customer_by_email(
                    cursor, 
                    customer_email=email_selector, 
                    new_name=new_name, 
                    new_email=new_email
                    )

        except service_exceptions.NotFoundError as e:
            ui.console.print(f"{e}", style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.ValidationError as e:
            ui.console.print(f"{e}", style="warning")
            raise typer.Exit(code=1)        
        except service_exceptions.ServiceError as e:
            ui.console.print(f"{e}", style="error")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)

    render_customers.print_customer_summary(updated_customer)
    


@customers_app.command("delete", help="Deletes a single customer in the database.")
def delete_customer_by_id(
    customer_id: int = typer.Option(..., "-i", "--id", help="ID of the customer."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            customers_services.delete_customer_by_id(cursor=cursor, customer_id=customer_id)

        except service_exceptions.ValidationError as e:
            ui.console.print(f"{e}", style="warning")
            raise typer.Exit(code=1)      
        except service_exceptions.NotFoundError as e:
            ui.console.print(f"{e}", style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:  
            ui.db_error(e)

    ui.console.print(f"Deleted customer (id={customer_id})", style="success")
