import sqlite3
import unittest
from user_invoice_db.db import schema, customers, invoices, reports

TEST_NAME_1 = "John Doe"
TEST_EMAIL_1 = "johndoe@gmail.com"
TEST_NAME_2 = "Alice"
TEST_EMAIL_2 = "alice@yahoo.org"
INVALID_CUSTOMER_ID = 9999

class TestCustomerCRUD(unittest.TestCase):

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

    # ---------- Customer CRUD Tests ----------
    def test_create_customer(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        row = self.cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['name'], TEST_NAME_1)
        self.assertEqual(row['email'], TEST_EMAIL_1)

    def test_get_customer_by_id(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        row = customers.get_customer_by_id(self.cursor, customer_id)
        self.assertEqual(row['id'], customer_id)

    def test_get_customer_by_email(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        row = customers.get_customer_by_email(self.cursor, TEST_EMAIL_1)
        self.assertIsNotNone(row)
        self.assertEqual(row['name'], TEST_NAME_1)
        self.assertEqual(row['email'], TEST_EMAIL_1)

    def test_get_customer_id_by_email(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        got_id = customers.get_customer_id_by_email(self.cursor, TEST_EMAIL_1)
        self.assertEqual(got_id, customer_id)

    def test_get_customer(self):
        customer_id_1 = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        customer_id_2 = customers.create_customer(self.cursor, TEST_NAME_2, TEST_EMAIL_2)
        rows = reports.get_customers(self.cursor)

        self.assertEqual(len(rows), 2)

        customer_1 = next((u for u in rows if u['id'] == customer_id_1), None)
        customer_2 = next((u for u in rows if u['id'] == customer_id_2), None)

        self.assertIsNotNone(customer_1)
        self.assertIsNotNone(customer_2)
        self.assertEqual(customer_1['name'], TEST_NAME_1)
        self.assertEqual(customer_1['email'], TEST_EMAIL_1)
        self.assertEqual(customer_2['name'], TEST_NAME_2)
        self.assertEqual(customer_2['email'], TEST_EMAIL_2)

    def test_get_customer_filter_by_min_total(self):
        customer_id_1 = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        customer_id_2 = customers.create_customer(self.cursor, TEST_NAME_2, TEST_EMAIL_2)
        invoice_id_1 = invoices.add_invoice_to_customer(self.cursor, customer_id_1, "1/1/2025", 200)
        invoice_id_2 = invoices.add_invoice_to_customer(self.cursor, customer_id_1, "1/1/2025", 300)

        rows = reports.get_customers(self.cursor, min_total_dollars=500)
        self.assertEqual(len(rows), 1)

        returned_ids = {r["id"] for r in rows}
        self.assertIn(customer_id_1, returned_ids)
        self.assertNotIn(customer_id_2, returned_ids)

    def test_update_customer_name_only(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)

        updated_name = "Timmy"
        customer_was_updated = customers.update_customer(self.cursor, customer_id, name=updated_name)
        updated_customer = customers.get_customer_by_id(self.cursor, customer_id)

        self.assertTrue(customer_was_updated)
        self.assertEqual(updated_customer['name'], updated_name)
        self.assertEqual(updated_customer['email'], TEST_EMAIL_1)

    def test_update_customer_email_only(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)

        updated_email = "paul@gmail.com"
        customer_was_updated = customers.update_customer(self.cursor, customer_id, email=updated_email)
        updated_customer = customers.get_customer_by_id(self.cursor, customer_id)
        
        self.assertTrue(customer_was_updated)
        self.assertEqual(updated_customer['name'], TEST_NAME_1)
        self.assertEqual(updated_customer['email'], updated_email)

    def test_update_customer_name_and_email(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)

        updated_name = "Melissa"
        updated_email = "melissa@test.co"
        customer_was_updated = customers.update_customer(self.cursor, customer_id, name=updated_name, email=updated_email)
        updated_customer = customers.get_customer_by_id(self.cursor, customer_id)

        self.assertTrue(customer_was_updated)
        self.assertEqual(updated_customer['name'], updated_name)
        self.assertEqual(updated_customer['email'], updated_email)

    def test_update_customer_no_fields_returns_false(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        self.assertFalse(customers.update_customer(self.cursor, customer_id))

    def test_delete_customer(self):
        customer_id = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)

        customer_was_deleted = customers.delete_customer(self.cursor, customer_id)
        row = customers.get_customer_by_id(self.cursor, customer_id)
        
        self.assertTrue(customer_was_deleted)
        self.assertIsNone(row)

    # ---------- Customer Validation ----------
    def test_create_customer_empty_name_raises(self):
        with self.assertRaises(ValueError):
            customers.create_customer(self.cursor, " ", "john@example.com")

    def test_create_customer_invalid_name_raises(self):
        with self.assertRaises(ValueError):
            customers.create_customer(self.cursor, "John 2 Doe", "johndoe@example.com")

    def test_create_customer_empty_email_raises(self):
        with self.assertRaises(ValueError):
            customers.create_customer(self.cursor, "John Doe", " ")

    def test_create_customer_invalid_email_raises(self):
        with self.assertRaises(ValueError):
            customers.create_customer(self.cursor, "John Doe", "invalid-email")

    def test_create_customer_duplicate_name_allowed(self):
        customer1_id = customers.create_customer(self.cursor, TEST_NAME_1, "first@example.com")
        customer2_id = customers.create_customer(self.cursor, TEST_NAME_1, "second@example.com")
        self.assertNotEqual(customer1_id, customer2_id)

    def test_create_customer_duplicate_email_raises(self):
        customers.create_customer(self.cursor, "John Doe", "same@example.com")
        with self.assertRaises(ValueError):
            customers.create_customer(self.cursor, "John Doe", "same@example.com")

    def test_update_customer_duplicate_email_raises(self):
        customer_id_1 = customers.create_customer(self.cursor, TEST_NAME_1, TEST_EMAIL_1)
        customer_id_2 = customers.create_customer(self.cursor, TEST_NAME_2, TEST_EMAIL_2)
        duplicate_email = TEST_EMAIL_1
        with self.assertRaises(ValueError):
            customers.update_customer(self.cursor, customer_id_2, email=duplicate_email)

    def test_delete_customer_invalid_id_returns_false(self):
        self.assertFalse(customers.delete_customer(self.cursor, INVALID_CUSTOMER_ID))

if __name__ == '__main__':
    unittest.main()