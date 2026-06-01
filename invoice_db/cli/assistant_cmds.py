# invoice_db/cli/assistant_cmds.py

import json
from typing import Annotated

import typer
from rich.console import Console

from invoice_db.assistant.data_source import ServiceInvoiceAssistantDataSource
from invoice_db.assistant.dispatcher import AssistantDispatcher
from invoice_db.assistant.router import AssistantRouter
from invoice_db.assistant.service import AssistantService
from invoice_db.assistant.classifier_router import ClassifierNotTrainedError
from invoice_db.db.connection import db_session
from invoice_db.services import exceptions

assistant_app = typer.Typer(help="Ask natural-language questions about invoices.")
console = Console()


@assistant_app.command()
def ask(
    message: Annotated[
        str,
        typer.Argument(help="Natural-language invoice question. Use quotes."),
    ],
    show_data: Annotated[
        bool,
        typer.Option("--show-data", help="Print raw response data as JSON."),
    ] = False,
) -> None:
    """Ask the assistant a natural-language invoice question."""

    try:
        with db_session() as (_, cursor):
            data_source = ServiceInvoiceAssistantDataSource(cursor)
            dispatcher = AssistantDispatcher(data_source)
            router = AssistantRouter()

            assistant = AssistantService(
                router=router,
                dispatcher=dispatcher,
                customer_name_provider=data_source,
            )

            response = assistant.ask(message)

        console.print(response.message)

        if show_data:
            console.print_json(
                json.dumps(
                    response.data,
                    indent=2,
                    default=str,
                )
            )

    except ClassifierNotTrainedError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    except (
        exceptions.ValidationError,
        exceptions.NotFoundError,
        exceptions.ServiceError,
    ) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc