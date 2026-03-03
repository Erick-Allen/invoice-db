from .utils import to_cents

# ----- REPORT / ANALYTICS -----#
def get_customers(cursor, min_total_dollars=0):
    min_cents = to_cents(min_total_dollars)
    cursor.execute("""
        SELECT 
            c.id, 
            c.name, 
            c.email, 
            COALESCE(SUM(i.total), 0) AS total
        FROM customers c
        LEFT JOIN invoices i ON i.customer_id = c.id
        GROUP BY c.id, c.name, c.email
        HAVING COALESCE(SUM(i.total), 0) >= ?
        ORDER BY c.id
    """, (min_cents,))
    return cursor.fetchall()

def get_customer_invoice_summary(cursor):
    """Return a list of customers with their invoice counts and total from view customer_invoice_summary"""
    cursor.execute("SELECT * FROM customer_invoice_summary ORDER BY customer_id")
    return cursor.fetchall()
