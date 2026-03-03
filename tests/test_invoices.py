import sqlite3
import unittest
from user_invoice_db.db import schema, customers, invoices, reports, utils

TEST_NAME_1 = "John Doe"
TEST_EMAIL_1 = "johndoe@gmail.com"
TEST_NAME_2 = "Alice"
TEST_EMAIL_2 = "alice@yahoo.org"
INVALID_CUSTOMER_ID = 9999
INVALID_INVOICE_ID = 8888
NEGATIVE_TOTAL = -9999

class TestInvoicesCRUD(unittest.TestCase):

    def setUp(self):
        self.connect = sqlite3.connect(":memory:")
        self.connect.row_factory = sqlite3.Row
        self.cursor = self.connect.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")

        schema.create_customer_schema(self.cursor)
        schema.create_invoice_schema(self.cursor)
        self.connect.commit()

    def tearDown(self):
        self.connect.close()

    # ---------- Invoice CRUD Tests ----------
    def test_create_invoice(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id = invoices.add_invoice_to_customer(self.cursor, customer_id, "1/20/2025", 300.25)
        row = self.cursor.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row['invoice_id'], invoice_id)
        self.assertEqual(row['customer_id'], customer_id)
        self.assertEqual(row['date_issued'], "2025-01-20")
        self.assertEqual(row['total'], 30025)
        self.assertIsNone(row["date_due"])

    def test_get_invoice_by_id(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id = invoices.add_invoice_to_customer(self.cursor, customer_id, "1/20/2025", 300.25)
        row = invoices.get_invoice_by_id(self.cursor, invoice_id)

        self.assertEqual(row['invoice_id'], invoice_id)

    def test_get_invoices_by_email(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = invoices.add_invoice_to_customer(self.cursor, customer_id, "1/20/2025", 300.25)
        invoice_id_2 = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/17/2025", 100)
        rows = invoices.get_invoices_by_email(self.cursor, TEST_EMAIL_1)

        self.assertEqual(len(rows), 2)

        invoice_1 = next((i for i in rows if i['invoice_id'] == invoice_id_1), None)
        invoice_2 = next((i for i in rows if i['invoice_id'] == invoice_id_2), None)
        
        self.assertIsNotNone(invoice_1)
        self.assertIsNotNone(invoice_2)
        self.assertEqual(invoice_1["customer_id"], customer_id)
        self.assertEqual(invoice_2["customer_id"], customer_id)
        self.assertEqual(invoice_1["invoice_id"], invoice_id_1)
        self.assertEqual(invoice_2["invoice_id"], invoice_id_2)

    def test_get_invoices_by_customer_id(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = invoices.add_invoice_to_customer(self.cursor, customer_id, "1/20/2025", 300.25)
        invoice_id_2 = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/17/2025", 100)
        rows = invoices.get_invoices_by_customer_id(self.cursor, customer_id)

        self.assertEqual(len(rows), 2)

        customer_ids = {r["customer_id"] for r in rows}
        self.assertEqual(customer_ids, {customer_id})

    def test_get_invoices_by_customer_and_range_inclusive(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = invoices.add_invoice_to_customer(self.cursor, customer_id, "1/20/2025", 300.25)
        invoice_id_2 = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/17/2025", 100)
        invoice_id_3 = invoices.add_invoice_to_customer(self.cursor, customer_id, "6/5/2025", 1000.01)

        start_date = "2/17/2025"
        end_date = "6/5/2025"
        rows = invoices.get_invoices_by_customer_and_range(self.cursor, customer_id, start_date, end_date)

        self.assertEqual(len(rows), 2)

        invoice_1 = next((i for i in rows if i['invoice_id'] == invoice_id_1), None)
        invoice_2 = next((i for i in rows if i['invoice_id'] == invoice_id_2), None)
        invoice_3 = next((i for i in rows if i['invoice_id'] == invoice_id_3), None)

        
        self.assertIsNone(invoice_1)
        self.assertIsNotNone(invoice_2)
        self.assertIsNotNone(invoice_3)
        self.assertEqual(invoice_2["customer_id"], customer_id)
        self.assertEqual(invoice_3["customer_id"], customer_id)
        self.assertEqual(invoice_2["invoice_id"], invoice_id_2)
        self.assertEqual(invoice_3["invoice_id"], invoice_id_3)

    def test_count_invoices(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = invoices.add_invoice_to_customer(self.cursor, customer_id, "1/20/2025", 300.25)
        invoice_id_2 = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/17/2025", 100)
        invoice_id_3 = invoices.add_invoice_to_customer(self.cursor, customer_id, "6/5/2025", 1000.01)

        invoice_count = invoices.count_invoices(self.cursor)

        self.assertEqual(invoice_count, 3)

    def test_update_invoice_date_issued_only(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = invoices.add_invoice_to_customer(self.cursor, customer_id, "1/20/2025", 300.25)
        invoice_id_2 = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/17/2025", 100)

        new_date_issued = "2025-03-08"
        updated = invoices.update_invoice(self.cursor, invoice_id_1, date_issued=new_date_issued)
        self.assertTrue(updated)

        row_1 = invoices.get_invoice_by_id(self.cursor, invoice_id_1)
        row_2 = invoices.get_invoice_by_id(self.cursor, invoice_id_2)

        self.assertEqual(row_1["date_issued"], new_date_issued)
        self.assertNotEqual(row_2["date_issued"], new_date_issued)

    def test_update_invoice_total_and_customer(self):
        customer_id_1 = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        customer_id_2 = customers.create_customer(self.cursor, TEST_NAME_2, TEST_EMAIL_2)
        invoice_id_1 = invoices.add_invoice_to_customer(self.cursor, customer_id_1, "1/20/2025", 300.25)
        invoice_id_2 = invoices.add_invoice_to_customer(self.cursor, customer_id_1, "2/17/2025", 100)

        new_total = 1500.90
        updated = invoices.update_invoice(self.cursor, invoice_id_2, total=new_total, customer_id=customer_id_2)
        self.assertTrue(updated)

        row_1 = invoices.get_invoice_by_id(self.cursor, invoice_id_1)
        row_2 = invoices.get_invoice_by_id(self.cursor, invoice_id_2)

        self.assertEqual(row_2["total"], utils.to_cents(new_total))
        self.assertEqual(row_2["customer_id"], customer_id_2)
        self.assertNotEqual(row_1["total"], utils.to_cents(new_total))
        self.assertEqual(row_1["customer_id"], customer_id_1)

    def test_update_invoice_no_fields_returns_false(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = invoices.add_invoice_to_customer(self.cursor, customer_id, "1/20/2025", 300.25)
        invoice_id_2 = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/17/2025", 100)

        updated = invoices.update_invoice(self.cursor, invoice_id_1)
        self.assertFalse(updated)

    def test_delete_invoice(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id_1 = invoices.add_invoice_to_customer(self.cursor, customer_id, "1/20/2025", 300.25)
        invoice_id_2 = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/17/2025", 100)

        deleted = invoices.delete_invoice(self.cursor, invoice_id_1)
        self.assertTrue(deleted)

        remaining = invoices.get_invoices_by_customer_id(self.cursor, customer_id)
        remaining_ids = {r["invoice_id"] for r in remaining}
        self.assertNotIn(invoice_id_1, remaining_ids)
        self.assertIn(invoice_id_2, remaining_ids)

    def test_delete_customer_cascades_invoices(self):
        customer_id = customers.create_customer(self.cursor, "John", "john@example.com")
        invoice = invoices.add_invoice_to_customer(self.cursor, customer_id, "1/1/2025", 100)
        deleted_customer = customers.delete_customer(self.cursor, customer_id)
        self.assertTrue(deleted_customer)

        cascaded_invoices = invoices.get_invoices_by_customer_id(self.cursor, customer_id)
        self.assertEqual(cascaded_invoices, [])

        row = customers.get_customer_by_id(self.cursor, customer_id)
        self.assertIsNone(row)

    # ---------- Invoice Validation ----------
    def test_create_invoice_invalid_customer_raises(self):
        with self.assertRaises(ValueError):
            invoices.add_invoice_to_customer(self.cursor, INVALID_CUSTOMER_ID, "1/1/2025", 100.25)

    def test_create_invoice_invalid_date_issued_raises(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        with self.assertRaises(ValueError):
            invoices.add_invoice_to_customer(self.cursor, customer_id, "invalid-date", 0)

    def test_create_invoice_negative_total_raises(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        with self.assertRaises(ValueError):
            invoices.add_invoice_to_customer(self.cursor, customer_id, "2/18/2025", NEGATIVE_TOTAL)

    def test_create_invoice_non_numeric_total_raises(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        with self.assertRaises(ValueError):
            invoices.add_invoice_to_customer(self.cursor, customer_id, "2/18/2025", "Test")
    
    def test_update_invoice_invalid_date_issued_raises(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/18/2025", 0)
        with self.assertRaises(ValueError):
            invoices.update_invoice(self.cursor, invoice_id, date_issued="invalid-date")

    def test_update_invoice_invalid_date_due_raises(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/18/2025", 0)
        with self.assertRaises(ValueError):
            invoices.update_invoice(self.cursor, invoice_id, date_due="invalid-date")

    def test_update_invoice_negative_total_raises(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/18/2025", 0)
        with self.assertRaises(ValueError):
            invoices.update_invoice(self.cursor, invoice_id, total=NEGATIVE_TOTAL)

    def test_update_invoice_invalid_customer_id_raises(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_id = invoices.add_invoice_to_customer(self.cursor, customer_id, "2/18/2025", 0)
        with self.assertRaises(ValueError):
            invoices.update_invoice(self.cursor, invoice_id, customer_id=INVALID_CUSTOMER_ID)

    def test_delete_invalid_invoice_id_returns_false(self):
        self.assertFalse(invoices.delete_invoice(self.cursor, INVALID_INVOICE_ID))

    def test_get_invoices_by_customer_and_range_invalid_start_raises(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        with self.assertRaises(ValueError):
            invoices.get_invoices_by_customer_and_range(self.cursor, customer_id, "invalid-date", "2/20/2025")

    def test_get_invoices_by_customer_and_range_invalid_end_raises(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        with self.assertRaises(ValueError):
            invoices.get_invoices_by_customer_and_range(self.cursor, customer_id, "2/20/2025", "invalid-date")


    def test_get_invoices_by_customer_id_empty_list(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        invoice_list = invoices.get_invoices_by_customer_id(self.cursor, customer_id)
        self.assertEqual(invoice_list, [])

if __name__ == '__main__':
    unittest.main()