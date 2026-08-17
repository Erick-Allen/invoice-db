from invoice_db.db.payments import VALID_PAYMENT_METHODS


def _sql_string_values(values: set[str]) -> str:
    return ", ".join(f"'{value}'" for value in sorted(values))


# TRIGGER
def create_triggers(cursor):
    cursor.executescript("""
    CREATE TRIGGER IF NOT EXISTS trigger_product_categories_updated
    AFTER UPDATE ON
        product_categories
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE product_categories
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;

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

    CREATE TRIGGER IF NOT EXISTS trigger_tags_updated
    AFTER UPDATE ON
        tags
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE tags
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

def create_tag_schema(cursor):
    cursor.executescript("""
    -- Tags table: reusable invoice context labels for reporting and filtering.
    CREATE TABLE IF NOT EXISTS tags (
        id              INTEGER PRIMARY KEY,
        name            TEXT    NOT NULL CHECK (length(trim(name)) > 0),
        description     TEXT,
        is_active       INTEGER NOT NULL DEFAULT 1
                                CHECK (is_active IN (0, 1)),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );

    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_tags_name_nocase ON tags(lower(name));
    CREATE INDEX IF NOT EXISTS
        idx_tags_is_active ON tags(is_active);

    -- Invoice tags table: many-to-many assignments between invoices and reusable tags.
    CREATE TABLE IF NOT EXISTS invoice_tags (
        invoice_id      INTEGER NOT NULL,
        tag_id          INTEGER NOT NULL,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        PRIMARY KEY (invoice_id, tag_id),
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE RESTRICT
    );

    CREATE INDEX IF NOT EXISTS
        idx_invoice_tags_invoice_id ON invoice_tags(invoice_id);
    CREATE INDEX IF NOT EXISTS
        idx_invoice_tags_tag_id ON invoice_tags(tag_id);
    """)

def create_product_category_schema(cursor):
    cursor.executescript("""
    -- Product categories table: reportable catalog buckets for products.
    CREATE TABLE IF NOT EXISTS product_categories (
        id              INTEGER PRIMARY KEY,
        name            TEXT    NOT NULL CHECK (length(trim(name)) > 0),
        description     TEXT,
        is_active       INTEGER NOT NULL DEFAULT 1
                                CHECK (is_active IN (0, 1)),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );

    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_product_categories_name_nocase ON product_categories(lower(name));
    CREATE INDEX IF NOT EXISTS
        idx_product_categories_is_active ON product_categories(is_active);

    INSERT OR IGNORE INTO product_categories (id, name, description, is_active)
    VALUES (1, 'Uncategorized', 'Default category for uncategorized products.', 1);
    """)

def create_product_schema(cursor):
    cursor.executescript("""
    -- Products table: reusable catalog items that can later be attached to invoice line items.
    CREATE TABLE IF NOT EXISTS products (
        id              INTEGER PRIMARY KEY,
        name            TEXT    NOT NULL CHECK (length(trim(name)) > 0),
        description     TEXT,
        cost            INTEGER NOT NULL DEFAULT 0
                                CHECK (cost >= 0 AND cost = CAST(cost AS INTEGER)),
        unit_price      INTEGER NOT NULL DEFAULT 0
                                CHECK (unit_price >= 0 AND unit_price = CAST(unit_price AS INTEGER)),
        category_id     INTEGER NOT NULL DEFAULT 1,
        is_active       INTEGER NOT NULL DEFAULT 1
                                CHECK (is_active IN (0, 1)),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (category_id) REFERENCES product_categories(id) ON DELETE RESTRICT
    );

    -- Support catalog lookup.
    CREATE INDEX IF NOT EXISTS
        idx_products_name ON products(name);
    CREATE INDEX IF NOT EXISTS
        idx_products_category_id ON products(category_id);
    CREATE INDEX IF NOT EXISTS
        idx_products_is_active ON products(is_active);
    """)
    cursor.execute("PRAGMA table_info(products)")
    columns = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if "category_id" not in columns:
        cursor.execute(
            "ALTER TABLE products ADD COLUMN category_id INTEGER NOT NULL DEFAULT 1"
        )
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
                idx_products_category_id ON products(category_id)
        """)
    if "cost" not in columns:
        cursor.execute(
            "ALTER TABLE products ADD COLUMN cost INTEGER NOT NULL DEFAULT 0"
        )

def create_invoice_item_schema(cursor):
    cursor.executescript("""
    -- Invoice items table: product-backed line items for invoices.
    CREATE TABLE IF NOT EXISTS invoice_items (
        id              INTEGER PRIMARY KEY,
        invoice_id      INTEGER NOT NULL,
        product_id      INTEGER NOT NULL,
        quantity        INTEGER NOT NULL DEFAULT 1
                                CHECK (quantity > 0 AND quantity = CAST(quantity AS INTEGER)),
        unit_cost       INTEGER NOT NULL DEFAULT 0
                                CHECK (unit_cost >= 0 AND unit_cost = CAST(unit_cost AS INTEGER)),
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
    cursor.execute("PRAGMA table_info(invoice_items)")
    columns = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if "unit_cost" not in columns:
        cursor.execute(
            "ALTER TABLE invoice_items ADD COLUMN unit_cost INTEGER NOT NULL DEFAULT 0"
        )
        cursor.execute("""
            UPDATE invoice_items
            SET unit_cost = COALESCE(
                (SELECT products.cost FROM products WHERE products.id = invoice_items.product_id),
                0
            )
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
    create_tag_schema(cursor)
    create_product_category_schema(cursor)
    create_product_schema(cursor)
    create_invoice_item_schema(cursor)
    create_payment_schema(cursor)
    create_customer_summary_view(cursor)
    create_triggers(cursor)
