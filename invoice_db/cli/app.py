import typer 
from .ui import console

    
#CLI APP
__version__ = "0.12.0"

app = typer.Typer(
    help=(
        "Command Line Interface for the customer_Invoice_Database.\n\n"
        "Use '--help' after any command for more details.\n\n"
        "Example: invoicedb --help"
        ),
    no_args_is_help=True
)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", "-v", 
        help="Show the CLI version and exit.",
        is_eager=True
    ),
):
    if version:
        console.print(f"customer_invoice_db CLI version [highlight]{__version__}[/highlight]")
        raise typer.Exit()

from .db_cmds import db_app
from .customers_cmds import customers_app
from .invoices_cmds import invoices_app
from .invoice_items_cmds import invoice_items_app
from .payments_cmds import payments_app
from .products_cmds import products_app
from .assistant_cmds import assistant_app

app.add_typer(db_app, name="db")
app.add_typer(customers_app, name="customers")
app.add_typer(invoices_app, name="invoices")
app.add_typer(invoice_items_app, name="invoice-items")
app.add_typer(payments_app, name="payments")
app.add_typer(products_app, name="products")
app.add_typer(assistant_app, name="assistant")
