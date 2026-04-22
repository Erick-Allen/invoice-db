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
        status = 'draft'
        OR (date_issued IS NOT NULL AND date_due IS NOT NULL)
    )    
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