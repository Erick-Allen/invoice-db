#!/bin/bash
source "$(dirname "$0")/seed.env"
VENV_ACTIVATE="$(dirname "$0")/../.venv/bin/activate"
if [ -f "$VENV_ACTIVATE" ]; then
  source "$VENV_ACTIVATE"
fi

get_id() {
    grep -m1 -o '[0-9]\+'
}

JOHN_ID=$(invoicedb customers get --email "$JOHN_EMAIL" | get_id)
ALICE_ID=$(invoicedb customers get --email "$ALICE_EMAIL" | get_id)
TOMMY_ID=$(invoicedb customers get --email "$TOMMY_EMAIL" | get_id)

invoicedb invoices create --id "$JOHN_ID" --total 400
invoicedb invoices create --id "$JOHN_ID" --total 100 --date-due "12/20/2026"
invoicedb invoices create --id "$ALICE_ID" --total 200 --date-due "12/30/2026"
invoicedb invoices create --id "$TOMMY_ID" --total 300 --date-due "10/11/2026"
