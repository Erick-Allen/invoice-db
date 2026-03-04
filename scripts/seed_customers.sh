#!/bin/bash
set -e
source "$(dirname "$0")/seed.env"
VENV_ACTIVATE="$(dirname "$0")/../.venv/bin/activate"
if [ -f "$VENV_ACTIVATE" ]; then
  source "$VENV_ACTIVATE"
fi

invoicedb customers create -n "John" -e $JOHN_EMAIL
invoicedb customers create -n "Alice" -e $ALICE_EMAIL
invoicedb customers create -n "Tommy" -e $TOMMY_EMAIL
