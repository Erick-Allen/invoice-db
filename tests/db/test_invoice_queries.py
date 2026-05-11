import pytest
from invoice_db.db import invoices

# ----------- INVOICE Count Tests -----------

def test_count_all_invoices(cursor, invoice_query_data):
    invoice_count = invoices.count_invoices(cursor)
    assert invoice_count == 4

def test_count_customer_invoices(cursor, invoice_query_data):
    john_id = invoice_query_data['customers']['john']
    invoice_count = invoices.count_invoices(cursor, customer_id=john_id)
    assert invoice_count == 2

@pytest.mark.parametrize("status", ["draft", "sent", "paid", "void"])
def test_count_invoices_filter_by_status(cursor, status, invoice_query_data):
    invoice_count = invoices.count_invoices(cursor, status=status)
    assert invoice_count == 1
    

def test_count_invoices_filter_by_min_total(cursor, invoice_query_data):
    invoice_count = invoices.count_invoices(cursor, min_total=250)
    assert invoice_count == 2

def test_count_invoices_filter_by_max_total(cursor, invoice_query_data):
    invoice_count = invoices.count_invoices(cursor, max_total=250)
    assert invoice_count == 3

def test_count_invoices_filters_by_multiple_values(cursor, invoice_query_data):
    alice_id = invoice_query_data['customers']['alice']
    invoice_count = invoices.count_invoices(cursor, customer_id=alice_id, status="paid", min_total=100.00)
    assert invoice_count == 1

# ----------- INVOICE Query Tests -----------
def test_list_invoices_returns_all(cursor, invoice_john, invoice_alice):
    result = invoices.list_invoices(cursor)
    found_ids = set(row['id'] for row in result)
    assert found_ids == {invoice_john, invoice_alice}

def test_list_invoices_empty_db_returns_empty_list(cursor):
    result = invoices.list_invoices(cursor)
    assert result == []

def test_list_invoices_filter_by_customer_id(cursor, customer_john, invoice_john, invoice_alice):
    results = invoices.list_invoices(cursor, customer_id=customer_john)
    found_ids = {row['id'] for row in results}
    assert len(results) == 1
    assert found_ids == {invoice_john}

@pytest.mark.parametrize("status", ["draft", "sent", "paid", "void"])
def test_list_invoices_filter_by_status(cursor, status, invoice_query_data):
    results = invoices.list_invoices(cursor, status=status)
    assert len(results) == 1
    assert results[0]['status'] == status
    

def test_list_invoices_filter_by_min_total(cursor, invoice_query_data):
    results = invoices.list_invoices(cursor, min_total=250)
    found_ids = {row['id'] for row in results}
    assert len(results) == 2
    assert all(row["total"] >= 25000 for row in results) #values return in cents fmt
    assert found_ids == {
        invoice_query_data['invoices']['john_sent'],
        invoice_query_data['invoices']['alice_paid'],
    }

def test_list_invoices_filter_by_max_total(cursor, invoice_query_data):
    results = invoices.list_invoices(cursor, max_total=250)
    found_ids = {row['id'] for row in results}
    assert len(results) == 3
    assert all(row["total"] <= 25000 for row in results)
    assert found_ids == {
        invoice_query_data['invoices']['john_draft'],
        invoice_query_data['invoices']['john_sent'],
        invoice_query_data['invoices']['alice_void'],
    }

def test_list_invoices_applies_limit(cursor, invoice_query_data):
    results = invoices.list_invoices(cursor, limit=2)
    assert len(results) == 2

def test_list_invoices_applies_offset(cursor, invoice_query_data):
    results = invoices.list_invoices(cursor, offset=1)
    assert len(results) == 3

# TODO: Break this down into seperate tests
@pytest.mark.parametrize("sort_by", ["id", "date_issued", "total", "status"])
def test_invoices_list_accepts_valid_sort_by_values(cursor, sort_by, invoice_query_data):
    results = invoices.list_invoices(cursor, sort_by=sort_by)
    assert len(results) == 4

#OVERDUE

def test_overdue_invoices_returns_only_overdue(cursor, invoice_overdue_data):
    results = invoices.list_overdue_invoices(cursor)
    found_ids = {row['id'] for row in results}
    assert len(results) == 2
    assert found_ids == {
        invoice_overdue_data['invoices']['john_overdue'],
        invoice_overdue_data['invoices']['alice_overdue'],
    }

def test_overdue_invoices_empty_db_returns_empty_list(cursor):
    result = invoices.list_overdue_invoices(cursor)
    assert result == []

def test_overdue_invoices_filters_by_customer_id(cursor, invoice_overdue_data):
    customer_id = invoice_overdue_data['customers']['john']
    results = invoices.list_overdue_invoices(cursor, customer_id=customer_id)
    found_id = {row['id'] for row in results}
    assert len(results) == 1
    assert found_id == {invoice_overdue_data['invoices']['john_overdue']}

def test_overdue_invoices_filters_by_min_total(cursor, invoice_overdue_data):
    result = invoices.list_overdue_invoices(cursor, min_total=400)
    found_id = {row['id'] for row in result}
    assert len(result) == 1
    assert all(row['total'] >= 40000 for row in result)
    assert found_id == {invoice_overdue_data['invoices']['alice_overdue']}

def test_overdue_invoices_filters_by_max_total(cursor, invoice_overdue_data):
    result = invoices.list_overdue_invoices(cursor, max_total=300)
    found_id = {row['id'] for row in result}
    assert len(result) == 1
    assert all(row['total'] <= 30000 for row in result)
    assert found_id == {invoice_overdue_data['invoices']['john_overdue']}

def test_overdue_invoices_applies_limit(cursor, invoice_overdue_data):
    results = invoices.list_overdue_invoices(cursor, limit=2)
    assert len(results) == 2

def test_overdue_invoices_applies_offset(cursor, invoice_overdue_data):
    results = invoices.list_overdue_invoices(cursor, offset=1)
    assert len(results) == 1

# TODO: Break this down into seperate tests
@pytest.mark.parametrize("sort_by", ["id", "date_issued", "date_due", "total", "days_overdue"])
def test_overdue_invoices_accepts_valid_sort_by_values(cursor, sort_by, invoice_overdue_data):
    results = invoices.list_overdue_invoices(cursor, sort_by=sort_by)
    assert len(results) == 2