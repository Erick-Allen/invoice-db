import typer, sqlite3
from typing import Optional

from invoice_db.db import connection
from invoice_db.services import customer_locations as location_services
from invoice_db.services import customers as customers_services
from invoice_db.services import exceptions as service_exceptions
from . import render_customer_locations, render_customers, ui

customers_app = typer.Typer(help="customer commands.")

@customers_app.command("create", help="Create and add a new customer to the database.")
def create_customer(
    customer_name: str = typer.Option(..., "-n", "--name", help="Name of the customer."),
    email: str = typer.Option(..., "-e", "--email", help="Email of the customer."),
    phone: Optional[str] = typer.Option(None, "--phone", help="Customer phone number."),
    customer_type: str = typer.Option("residential", "--type", help="residential | commercial | property_manager | other"),
    company_name: Optional[str] = typer.Option(None, "--company", help="Company name for non-residential customers."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            customer = customers_services.create_customer(
                cursor,
                customer_name,
                email,
                phone=phone,
                customer_type=customer_type,
                company_name=company_name,
            )

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
    new_phone: Optional[str] = typer.Option(None, "--phone", help="Phone to update customer with."),
    new_customer_type: Optional[str] = typer.Option(None, "--type", help="residential | commercial | property_manager | other"),
    new_company_name: Optional[str] = typer.Option(None, "--company", help="Company name for non-residential customers."),
    new_is_active: Optional[bool] = typer.Option(None, "--active/--inactive", help="Set customer active status."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB.")
):
    updated_customer = None

    if id is None and email_selector is None:
        ui.console.print("Please provide either --id or --email to select a customer", style="warning")
        raise typer.Exit(code=1)
    if id is not None and email_selector is not None:
        ui.console.print("Please provide only one of --id or --email (not both)", style="warning")
        raise typer.Exit(code=1)
    if (
        new_name is None
        and new_email is None
        and new_phone is None
        and new_customer_type is None
        and new_company_name is None
        and new_is_active is None
    ):
        ui.console.print("Please provide at least one customer field to update", style="warning")
        raise typer.Exit(code=1)
    
    with connection.db_session(db_path) as (connect, cursor):
        try:
            if id is not None:
                updated_customer = customers_services.update_customer_by_id(
                    cursor, 
                    customer_id=id, 
                    new_name=new_name, 
                    new_email=new_email,
                    new_phone=new_phone,
                    new_customer_type=new_customer_type,
                    new_company_name=new_company_name,
                    new_is_active=new_is_active,
                    )
            else:
                updated_customer = customers_services.update_customer_by_email(
                    cursor, 
                    customer_email=email_selector, 
                    new_name=new_name, 
                    new_email=new_email,
                    new_phone=new_phone,
                    new_customer_type=new_customer_type,
                    new_company_name=new_company_name,
                    new_is_active=new_is_active,
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


@customers_app.command("add-location", help="Add a location to a customer.")
def add_customer_location(
    customer_id: int = typer.Option(..., "-c", "--customer-id", help="Customer ID."),
    label: str = typer.Option(..., "--label", help="Location label."),
    address_line1: str = typer.Option(..., "--address-line1", help="Address line 1."),
    city: str = typer.Option(..., "--city", help="City."),
    state: str = typer.Option(..., "--state", help="State."),
    postal_code: str = typer.Option(..., "--postal-code", help="Postal or ZIP code."),
    address_line2: Optional[str] = typer.Option(None, "--address-line2", help="Address line 2."),
    country: str = typer.Option("US", "--country", help="Country."),
    is_primary: bool = typer.Option(False, "--primary/--not-primary", help="Mark as primary location."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Internal location notes."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            location = location_services.create_customer_location(
                cursor,
                customer_id=customer_id,
                label=label,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                is_primary=is_primary,
                notes=notes,
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

    ui.console.print(f"Created customer location (id={location['id']})", style="success")
    render_customer_locations.print_customer_location(location)


@customers_app.command("list-locations", help="List locations for a customer.")
def list_customer_locations(
    customer_id: int = typer.Option(..., "-c", "--customer-id", help="Customer ID."),
    active_only: bool = typer.Option(False, "--active-only", help="Only show active locations."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            locations = location_services.list_customer_locations(
                cursor,
                customer_id=customer_id,
                active_only=active_only,
            )
        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)

    if locations:
        render_customer_locations.print_customer_locations_table(locations)
    else:
        render_customer_locations.no_customer_locations_found()


@customers_app.command("update-location", help="Update a customer location.")
def update_customer_location(
    customer_id: int = typer.Option(..., "-c", "--customer-id", help="Customer ID."),
    location_id: int = typer.Option(..., "-l", "--location-id", help="Customer location ID."),
    label: Optional[str] = typer.Option(None, "--label", help="Location label."),
    address_line1: Optional[str] = typer.Option(None, "--address-line1", help="Address line 1."),
    address_line2: Optional[str] = typer.Option(None, "--address-line2", help="Address line 2."),
    city: Optional[str] = typer.Option(None, "--city", help="City."),
    state: Optional[str] = typer.Option(None, "--state", help="State."),
    postal_code: Optional[str] = typer.Option(None, "--postal-code", help="Postal or ZIP code."),
    country: Optional[str] = typer.Option(None, "--country", help="Country."),
    is_primary: Optional[bool] = typer.Option(None, "--primary/--not-primary", help="Set primary status."),
    is_active: Optional[bool] = typer.Option(None, "--active/--inactive", help="Set active status."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Internal location notes."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            location = location_services.update_customer_location_by_id(
                cursor,
                customer_id=customer_id,
                location_id=location_id,
                label=label,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                is_primary=is_primary,
                is_active=is_active,
                notes=notes,
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

    ui.console.print(f"Updated customer location (id={location['id']})", style="success")
    render_customer_locations.print_customer_location(location)


@customers_app.command("deactivate-location", help="Deactivate a customer location.")
def deactivate_customer_location(
    customer_id: int = typer.Option(..., "-c", "--customer-id", help="Customer ID."),
    location_id: int = typer.Option(..., "-l", "--location-id", help="Customer location ID."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            location = location_services.deactivate_customer_location(
                cursor,
                customer_id=customer_id,
                location_id=location_id,
            )
        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deactivated customer location (id={location['id']})", style="success")


@customers_app.command("delete-location", help="Delete a customer location.")
def delete_customer_location(
    customer_id: int = typer.Option(..., "-c", "--customer-id", help="Customer ID."),
    location_id: int = typer.Option(..., "-l", "--location-id", help="Customer location ID."),
    db_path: str = typer.Option(connection.DB_PATH, "--db", help="Path to SQLite DB."),
):
    with connection.db_session(db_path) as (connect, cursor):
        try:
            location_services.delete_customer_location(
                cursor,
                customer_id=customer_id,
                location_id=location_id,
            )
        except service_exceptions.ValidationError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.NotFoundError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except service_exceptions.ConflictError as e:
            ui.console.print(str(e), style="warning")
            raise typer.Exit(code=1)
        except sqlite3.Error as e:
            ui.db_error(e)

    ui.console.print(f"Deleted customer location (id={location_id})", style="success")
