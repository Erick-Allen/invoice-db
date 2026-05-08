import typer
from rich.theme import Theme
from rich.console import Console
from contextlib import contextmanager

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

def db_error(e: Exception) -> None:
    console.print(f"Database error: {e}", style="error")
    raise typer.Exit(code=1)