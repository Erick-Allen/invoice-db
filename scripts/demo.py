import subprocess
import time
import msvcrt
import argparse
from datetime import date
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument(
    "--live",
    action="store_true",
    help="Pause between sections and wait for a key press.",
)
args = parser.parse_args()

DB_PATH = "demo.sqlite"
TYPE_DELAY = 0.06
TODAY = date.today().isoformat()
LIVE_MODE = args.live

def type_text(text, delay=TYPE_DELAY):
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()

def display_command(args):
    parts = []
    for arg in args:
        if " " in arg:
            parts.append(f'"{arg}"')
        else:
            parts.append(arg)
    return " ".join(parts)

def run_command(args):
    type_text(f"$ {display_command(args)}")
    time.sleep(0.4)
    subprocess.run(args, check=True)

def pause_between_sections(pause_seconds, next_title=None):
    if LIVE_MODE:
        message = "Press any key to continue"
        if next_title:
            message += f" -> {next_title}"
        message += "..."
        print(message, end="", flush=True)
        msvcrt.getch()
        print("\n")
    else:
        print()
        time.sleep(pause_seconds)


db_file = Path(DB_PATH)
if db_file.exists():
    db_file.unlink()

sections = [
    {
        "title": "Initialize the database",
        "commands": [
            ["invoicedb", "db", "init", "--db", DB_PATH],
        ],
        "pause": 1.0,
    },
    {
        "title": "Create customers",
        "commands": [
            ["invoicedb", "customers", "create", "--name", "Alice Johnson", "--email", "alice@example.com", "--db", DB_PATH],
            ["invoicedb", "customers", "create", "--name", "John Doe", "--email", "john@example.com", "--db", DB_PATH],
        ],
        "pause": 2.0,
    },
    {
        "title": "Create invoices",
        "commands": [
            ["invoicedb", "invoices", "create", "--customer-id", "1", "--total", "2500", "--db", DB_PATH],
            ["invoicedb", "invoices", "create", "--customer-id", "2", "--total", "400.25", "--db", DB_PATH],
            ["invoicedb", "invoices", "create", "--customer-id", "2", "--date-issued", "03/01/2026", "--date-due", "04/01/2026", "--total", "1100", "--db", DB_PATH],
        ],
        "pause": 2.0,
    },
    {
        "title": "List invoices created",
        "commands": [
            ["invoicedb", "invoices", "list", "--db", DB_PATH], 
        ],
        "pause": 5.0,
    },
    {
        "title": "Update Invoices",
        "commands": [
            ["invoicedb", "invoices", "set-status", "--id", "1", "--status", "sent", "--db", DB_PATH],
            ["invoicedb", "invoices", "update", "--id", "3", "--total", "800.50", "--db", DB_PATH],
            ["invoicedb", "invoices", "set-status", "--id", "3", "--status", "sent", "--db", DB_PATH],
        ],
        "pause": 4.0,
    },
    {
        "title": "Count Filtered Invoices",
        "commands": [
            ["invoicedb", "invoices", "count", "--status", "sent", "--min-total", "100", "--db", DB_PATH]
        ],
        "pause": 5.0,
    },
    {
        "title": "List John's invoices sorted by total",
        "commands": [
            ["invoicedb", "invoices", "list", "--customer-id", "2", "--sort-by", "total", "--asc", "--db", DB_PATH],
        ],
        "pause": 5.0,
    },
     {
        "title": f"Overdue invoices (as of {TODAY})",
        "commands": [
            ["invoicedb", "invoices", "overdue", "--db", DB_PATH],
        ],
        "pause": 5.0,
    },
    {
        "title": "Delete Invoice",
        "commands": [
            ["invoicedb", "invoices", "delete", "--id", "2", "--db", DB_PATH],
        ],
        "pause": 4.0
    },
    {
        "title": "Final State",
        "commands": [
            ["invoicedb", "invoices", "list", "--db", DB_PATH], 
        ],
        "pause": 5.0
    },


]

for i, section in enumerate(sections):
    print(f"---------- {(section)['title'].upper()} ----------")
    time.sleep(0.5)
    
    for command in section["commands"]:
        run_command(command)

    next_title = sections[i + 1]["title"] if i < len(sections) - 1 else None
    pause_between_sections(section["pause"], next_title)