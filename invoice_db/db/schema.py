from invoice_db.db.payments import VALID_PAYMENT_METHODS


def _sql_string_values(values: set[str]) -> str:
    return ", ".join(f"'{value}'" for value in sorted(values))


# TRIGGER
def create_triggers(cursor):
    cursor.executescript("""
    CREATE TRIGGER IF NOT EXISTS trigger_customers_updated
    AFTER UPDATE ON 
        customers
    WHEN 
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE customers
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;
                         
    CREATE TRIGGER IF NOT EXISTS trigger_invoices_updated
    AFTER UPDATE ON
        invoices
    WHEN 
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE invoices
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;

    CREATE TRIGGER IF NOT EXISTS trigger_products_updated
    AFTER UPDATE ON
        products
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE products
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;

    CREATE TRIGGER IF NOT EXISTS trigger_invoice_items_updated
    AFTER UPDATE ON
        invoice_items
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE invoice_items
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;

    CREATE TRIGGER IF NOT EXISTS trigger_payments_updated
    AFTER UPDATE ON
        payments
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE payments
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;
    """)

# TABLE CREATION
def create_customer_schema(cursor):
    cursor.executescript("""
    -- Customers table: stores basic account information.                       
    CREATE TABLE IF NOT EXISTS customers (
        id          INTEGER PRIMARY KEY,
        name        TEXT    NOT NULL CHECK (length(trim(name)) > 0),
        email       TEXT    NOT NULL CHECK (length(trim(email)) > 0 ),
        created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );
    
    -- Enforce case-insensitive unique emails & index customer names.
    CREATE UNIQUE INDEX IF NOT EXISTS 
        idx_customers_email_nocase ON customers(lower(email));
    CREATE INDEX IF NOT EXISTS
        idx_customers_name ON customers(name);
    """)

def create_invoice_schema(cursor):
    cursor.executescript("""
    -- Invoices table: records all invoices linked to a customer.
    CREATE TABLE IF NOT EXISTS invoices (
        id              INTEGER PRIMARY KEY,
        customer_id     INTEGER NOT NULL,
        date_issued     TEXT,
        date_due        TEXT,
        total           INTEGER NOT NULL DEFAULT 0 
                        CHECK (total >= 0 AND total = CAST(total AS INTEGER)),
        status          TEXT    NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft','sent','paid','void')),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK (
        date_issued IS NULL
        OR date_due IS NULL
        OR date_issued <= date_due                     
    )
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE -- deletes invoices when customer removed
    );
                         
    -- Index frequent queries and filtering patterns.
    CREATE INDEX IF NOT EXISTS 
        idx_invoices_customer_id ON invoices(customer_id);                         
    CREATE INDEX IF NOT EXISTS 
        idx_invoices_date_issued ON invoices(date_issued);
    CREATE INDEX IF NOT EXISTS 
        idx_invoices_date_due ON invoices(date_due);
    CREATE INDEX IF NOT EXISTS 
        idx_invoices_customer_date ON invoices(customer_id, date_issued);
    """)

def create_product_schema(cursor):
    cursor.executescript("""
    -- Products table: reusable catalog items that can later be attached to invoice line items.
    CREATE TABLE IF NOT EXISTS products (
        id              INTEGER PRIMARY KEY,
        name            TEXT    NOT NULL CHECK (length(trim(name)) > 0),
        description     TEXT,
        unit_price      INTEGER NOT NULL DEFAULT 0
                                CHECK (unit_price >= 0 AND unit_price = CAST(unit_price AS INTEGER)),
        is_active       INTEGER NOT NULL DEFAULT 1
                                CHECK (is_active IN (0, 1)),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );

    -- Support catalog lookup.
    CREATE INDEX IF NOT EXISTS
        idx_products_name ON products(name);
    CREATE INDEX IF NOT EXISTS
        idx_products_is_active ON products(is_active);
    """)

def create_invoice_item_schema(cursor):
    cursor.executescript("""
    -- Invoice items table: product-backed line items for invoices.
    CREATE TABLE IF NOT EXISTS invoice_items (
        id              INTEGER PRIMARY KEY,
        invoice_id      INTEGER NOT NULL,
        product_id      INTEGER NOT NULL,
        quantity        INTEGER NOT NULL DEFAULT 1
                                CHECK (quantity > 0 AND quantity = CAST(quantity AS INTEGER)),
        unit_price      INTEGER NOT NULL
                                CHECK (unit_price >= 0 AND unit_price = CAST(unit_price AS INTEGER)),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
    );

    CREATE INDEX IF NOT EXISTS
        idx_invoice_items_invoice_id ON invoice_items(invoice_id);
    CREATE INDEX IF NOT EXISTS
        idx_invoice_items_product_id ON invoice_items(product_id);
    CREATE INDEX IF NOT EXISTS
        idx_invoice_items_invoice_product ON invoice_items(invoice_id, product_id);
    """)

def create_payment_schema(cursor):
    payment_methods = _sql_string_values(VALID_PAYMENT_METHODS)
    cursor.executescript(f"""
    -- Payments table: records money received against invoices.
    CREATE TABLE IF NOT EXISTS payments (
        id              INTEGER PRIMARY KEY,
        invoice_id      INTEGER NOT NULL,
        amount_cents    INTEGER NOT NULL
                                CHECK (amount_cents > 0 AND amount_cents = CAST(amount_cents AS INTEGER)),
        payment_date    TEXT    NOT NULL CHECK (length(trim(payment_date)) > 0),
        method          TEXT    NOT NULL CHECK (method IN ({payment_methods})),
        note            TEXT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS
        idx_payments_invoice_id ON payments(invoice_id);
    CREATE INDEX IF NOT EXISTS
        idx_payments_payment_date ON payments(payment_date);
    CREATE INDEX IF NOT EXISTS
        idx_payments_method ON payments(method);
    """)

def create_customer_summary_view(cursor):
    cursor.executescript("""
    CREATE VIEW IF NOT EXISTS customer_invoice_summary AS
    SELECT
        c.id AS customer_id,
        c.name, 
        c.email,
        COUNT(i.id) AS invoice_count,
        COALESCE(SUM(i.total), 0) AS total_cents
    FROM 
        customers c
    LEFT JOIN 
        invoices i ON i.customer_id = c.id
    GROUP BY 
        c.id, c.name, c.email;
    """)

def create_schema(cursor):
    create_customer_schema(cursor)
    create_invoice_schema(cursor)
    create_product_schema(cursor)
    create_invoice_item_schema(cursor)
    create_payment_schema(cursor)
    create_customer_summary_view(cursor)
    create_triggers(cursor)
