#!/bin/bash
set -e
export INVOICEDB_PATH="$(dirname "$0")/../demo.sqlite"
source "$(dirname "$0")/seed.env"
#VENV_ACTIVATE="$(dirname "$0")/../.venv/bin/activate" #Mac
VENV_ACTIVATE="$(dirname "$0")/../.venv/Scripts/activate" #Windows
if [ -f "$VENV_ACTIVATE" ]; then
  source "$VENV_ACTIVATE"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

"$SCRIPT_DIR/reset.sh"
echo

echo "Creating customers..."
"$SCRIPT_DIR/seed_customers.sh"
echo

echo "Creating invoices..."
"$SCRIPT_DIR/seed_invoices.sh"
echo

echo "===== INITIAL CUSTOMERS AND INVOICES ====="
invoicedb invoices list
echo 

JOHN_ID=$(invoicedb customers get --email "$JOHN_EMAIL" | grep -m1 -o '[0-9]\+')
: "${JOHN_ID:?Failed to resolve JOHN_ID}"

INVOICE_ID=$(invoicedb invoices list --customer-id "$JOHN_ID" | grep -m1 -o '[0-9]\+')
: "${INVOICE_ID:?Failed to resolve INVOICE_ID}"

echo "===== UPDATE INVOICE TOTAL & DATE DUE ====="
invoicedb invoices update --id "$INVOICE_ID" --total 1234 --date-due 8/12/2026
echo

echo "===== UPDATE JOHN ====="
invoicedb customers update --id "$JOHN_ID" --name "Willam" --new-email "willam@hotmail.com"
echo

ALICE_ID=$(invoicedb customers get --email "$ALICE_EMAIL" | grep -m1 -o '[0-9]\+')
: "${ALICE_ID:?Failed to resolve ALICE_ID}"

echo "===== DELETE ALICE ====="
invoicedb customers delete --id "$ALICE_ID"
echo

echo "===== FINAL USERS AND INVOICES ====="
invoicedb invoices list
echo

echo "Done."