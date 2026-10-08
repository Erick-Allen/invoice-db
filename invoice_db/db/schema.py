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

    CREATE TRIGGER IF NOT EXISTS trigger_business_profiles_updated
    AFTER UPDATE ON
        business_profiles
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE business_profiles
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;

    CREATE TRIGGER IF NOT EXISTS trigger_customer_locations_updated
    AFTER UPDATE ON
        customer_locations
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE customer_locations
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;

    CREATE TRIGGER IF NOT EXISTS trigger_supplier_locations_updated
    AFTER UPDATE ON
        supplier_locations
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE supplier_locations
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;

    CREATE TRIGGER IF NOT EXISTS trigger_locations_updated
    AFTER UPDATE ON
        locations
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE locations
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

    CREATE TRIGGER IF NOT EXISTS trigger_suppliers_updated
    AFTER UPDATE ON
        suppliers
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE suppliers
        SET updated_at = datetime('now', 'localtime')
        WHERE id = NEW.id;
    END;

    CREATE TRIGGER IF NOT EXISTS trigger_product_suppliers_updated
    AFTER UPDATE ON
        product_suppliers
    WHEN
        NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE product_suppliers
        SET updated_at = datetime('now', 'localtime')
        WHERE product_id = NEW.product_id
          AND supplier_id = NEW.supplier_id;
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
def create_workspace_schema(cursor):
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS workspaces (
        id              INTEGER PRIMARY KEY,
        name            TEXT    NOT NULL CHECK (length(trim(name)) > 0),
        owner_user_id   INTEGER NOT NULL,
        is_guest        INTEGER NOT NULL DEFAULT 0 CHECK (is_guest IN (0, 1)),
        expires_at      TEXT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
    );

    CREATE INDEX IF NOT EXISTS
        idx_workspaces_owner_user_id ON workspaces(owner_user_id);
    """)
    cursor.execute("PRAGMA table_info(workspaces)")
    columns = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if "is_guest" not in columns:
        cursor.execute(
            "ALTER TABLE workspaces ADD COLUMN is_guest INTEGER NOT NULL DEFAULT 0"
        )
    if "expires_at" not in columns:
        cursor.execute("ALTER TABLE workspaces ADD COLUMN expires_at TEXT")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_workspaces_guest_expires_at ON workspaces(is_guest, expires_at)"
    )

def create_business_profile_schema(cursor):
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS business_profiles (
        id                      INTEGER PRIMARY KEY,
        workspace_id            INTEGER NOT NULL UNIQUE,
        business_name           TEXT,
        email                   TEXT,
        phone                   TEXT,
        website                 TEXT,
        address_line1           TEXT,
        address_line2           TEXT,
        city                    TEXT,
        state                   TEXT,
        postal_code             TEXT,
        default_payment_terms_days INTEGER CHECK (
                                    default_payment_terms_days IS NULL
                                    OR default_payment_terms_days >= 0
                                ),
        ways_to_pay            TEXT,
        default_tax_rate       TEXT,
        default_invoice_footer  TEXT,
        logo_url                TEXT,
        created_at              TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at              TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS
        idx_business_profiles_workspace_id ON business_profiles(workspace_id);
    """)
    cursor.execute("PRAGMA table_info(business_profiles)")
    columns = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if "default_payment_terms_days" not in columns:
        cursor.execute(
            """
            ALTER TABLE business_profiles
            ADD COLUMN default_payment_terms_days INTEGER CHECK (
                default_payment_terms_days IS NULL
                OR default_payment_terms_days >= 0
            )
            """
        )
    if "ways_to_pay" not in columns:
        cursor.execute("ALTER TABLE business_profiles ADD COLUMN ways_to_pay TEXT")
    if "default_tax_rate" not in columns:
        cursor.execute("ALTER TABLE business_profiles ADD COLUMN default_tax_rate TEXT")

def create_customer_schema(cursor):
    cursor.executescript("""
    -- Customers table: stores basic account information.                       
    CREATE TABLE IF NOT EXISTS customers (
        id              INTEGER PRIMARY KEY,
        workspace_id    INTEGER,
        name            TEXT    NOT NULL CHECK (length(trim(name)) > 0),
        email           TEXT    NOT NULL CHECK (length(trim(email)) > 0),
        phone           TEXT,
        customer_type   TEXT    NOT NULL DEFAULT 'residential'
                                CHECK (customer_type IN ('residential', 'commercial', 'property_manager', 'other')),
        company_name    TEXT,
        is_active       INTEGER NOT NULL DEFAULT 1
                                CHECK (is_active IN (0, 1)),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );

    -- Enforce case-insensitive unique emails & index customer names.
    CREATE INDEX IF NOT EXISTS
        idx_customers_name ON customers(name);
    CREATE INDEX IF NOT EXISTS
        idx_customers_is_active ON customers(is_active);
    """)
    cursor.execute("PRAGMA table_info(customers)")
    columns = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if "workspace_id" not in columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN workspace_id INTEGER")

    cursor.execute("DROP INDEX IF EXISTS idx_customers_email_nocase")
    cursor.executescript("""
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_customers_unowned_email_nocase
        ON customers(lower(email))
        WHERE workspace_id IS NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_customers_workspace_email_nocase
        ON customers(workspace_id, lower(email))
        WHERE workspace_id IS NOT NULL;

    CREATE INDEX IF NOT EXISTS
        idx_customers_workspace_id ON customers(workspace_id);
    """)

def create_invoice_schema(cursor):
    cursor.executescript("""
    -- Invoices table: records all invoices linked to a customer.
    CREATE TABLE IF NOT EXISTS invoices (
        id              INTEGER PRIMARY KEY,
        workspace_id    INTEGER,
        invoice_number  INTEGER CHECK (invoice_number IS NULL OR invoice_number > 0),
        customer_id     INTEGER NOT NULL,
        location_id     INTEGER,
        title           TEXT,
        description     TEXT,
        date_issued     TEXT,
        date_due        TEXT,
        subtotal_cents  INTEGER NOT NULL DEFAULT 0
                        CHECK (subtotal_cents >= 0 AND subtotal_cents = CAST(subtotal_cents AS INTEGER)),
        tax_rate        TEXT,
        tax_cents       INTEGER NOT NULL DEFAULT 0
                        CHECK (tax_cents >= 0 AND tax_cents = CAST(tax_cents AS INTEGER)),
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
    ),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES customer_locations(id) ON DELETE SET NULL
    );
                         
    -- Index frequent queries and filtering patterns.
    CREATE INDEX IF NOT EXISTS 
        idx_invoices_customer_id ON invoices(customer_id);                         
    CREATE INDEX IF NOT EXISTS
        idx_invoices_location_id ON invoices(location_id);
    CREATE INDEX IF NOT EXISTS 
        idx_invoices_date_issued ON invoices(date_issued);
    CREATE INDEX IF NOT EXISTS 
        idx_invoices_date_due ON invoices(date_due);
    CREATE INDEX IF NOT EXISTS 
        idx_invoices_customer_date ON invoices(customer_id, date_issued);
    """)
    cursor.execute("PRAGMA table_info(invoices)")
    columns = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if "workspace_id" not in columns:
        cursor.execute("ALTER TABLE invoices ADD COLUMN workspace_id INTEGER")
    if "invoice_number" not in columns:
        cursor.execute("ALTER TABLE invoices ADD COLUMN invoice_number INTEGER")
    if "title" not in columns:
        cursor.execute("ALTER TABLE invoices ADD COLUMN title TEXT")
    if "description" not in columns:
        cursor.execute("ALTER TABLE invoices ADD COLUMN description TEXT")
    if "subtotal_cents" not in columns:
        cursor.execute("ALTER TABLE invoices ADD COLUMN subtotal_cents INTEGER NOT NULL DEFAULT 0")
        cursor.execute("UPDATE invoices SET subtotal_cents = total WHERE total > 0")
    if "tax_rate" not in columns:
        cursor.execute("ALTER TABLE invoices ADD COLUMN tax_rate TEXT")
    if "tax_cents" not in columns:
        cursor.execute("ALTER TABLE invoices ADD COLUMN tax_cents INTEGER NOT NULL DEFAULT 0")
    cursor.execute("PRAGMA index_list(invoices)")
    indexes = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if (
        "idx_invoices_unowned_invoice_number" not in indexes
        or "idx_invoices_workspace_invoice_number" not in indexes
    ):
        cursor.executescript("""
        WITH numbered AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY workspace_id
                    ORDER BY id
                ) AS next_invoice_number
            FROM invoices
        )
        UPDATE invoices
        SET invoice_number = (
            SELECT next_invoice_number
            FROM numbered
            WHERE numbered.id = invoices.id
        );
        """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_invoices_workspace_id ON invoices(workspace_id)"
    )
    cursor.executescript("""
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_invoices_unowned_invoice_number
        ON invoices(invoice_number)
        WHERE workspace_id IS NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_invoices_workspace_invoice_number
        ON invoices(workspace_id, invoice_number)
        WHERE workspace_id IS NOT NULL;
    """)

def create_location_schema(cursor):
    cursor.executescript("""
    -- Locations table: stores reusable physical addresses scoped to a workspace when signed in.
    CREATE TABLE IF NOT EXISTS locations (
        id              INTEGER PRIMARY KEY,
        workspace_id    INTEGER,
        address_line1   TEXT    NOT NULL CHECK (length(trim(address_line1)) > 0),
        address_line2   TEXT,
        city            TEXT    NOT NULL CHECK (length(trim(city)) > 0),
        state           TEXT    NOT NULL CHECK (length(trim(state)) > 0),
        postal_code     TEXT    NOT NULL CHECK (length(trim(postal_code)) > 0),
        country         TEXT    NOT NULL DEFAULT 'US' CHECK (length(trim(country)) > 0),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS
        idx_locations_postal_code ON locations(postal_code);
    """)
    cursor.execute("PRAGMA table_info(locations)")
    columns = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if "workspace_id" not in columns:
        cursor.execute("ALTER TABLE locations ADD COLUMN workspace_id INTEGER")

    cursor.execute("DROP INDEX IF EXISTS idx_locations_unique_address")
    cursor.executescript("""
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_locations_unowned_unique_address
        ON locations(
            lower(trim(address_line1)),
            lower(trim(COALESCE(address_line2, ''))),
            lower(trim(city)),
            lower(trim(state)),
            lower(trim(postal_code)),
            lower(trim(country))
        )
        WHERE workspace_id IS NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_locations_workspace_unique_address
        ON locations(
            workspace_id,
            lower(trim(address_line1)),
            lower(trim(COALESCE(address_line2, ''))),
            lower(trim(city)),
            lower(trim(state)),
            lower(trim(postal_code)),
            lower(trim(country))
        )
        WHERE workspace_id IS NOT NULL;

    CREATE INDEX IF NOT EXISTS
        idx_locations_workspace_id ON locations(workspace_id);
    """)


def create_customer_location_schema(cursor):
    cursor.executescript("""
    -- Customer locations table: links customers to reusable service/billing/job addresses.
    CREATE TABLE IF NOT EXISTS customer_locations (
        id              INTEGER PRIMARY KEY,
        customer_id     INTEGER NOT NULL,
        location_id     INTEGER NOT NULL,
        label           TEXT    NOT NULL CHECK (length(trim(label)) > 0),
        is_primary      INTEGER NOT NULL DEFAULT 0
                                CHECK (is_primary IN (0, 1)),
        is_active       INTEGER NOT NULL DEFAULT 1
                                CHECK (is_active IN (0, 1)),
        notes           TEXT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
        FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE RESTRICT
    );

    CREATE INDEX IF NOT EXISTS
        idx_customer_locations_customer_id ON customer_locations(customer_id);
    CREATE INDEX IF NOT EXISTS
        idx_customer_locations_location_id ON customer_locations(location_id);
    CREATE INDEX IF NOT EXISTS
        idx_customer_locations_is_active ON customer_locations(is_active);
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_customer_locations_customer_location
        ON customer_locations(customer_id, location_id);
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_customer_locations_one_primary
        ON customer_locations(customer_id)
        WHERE is_primary = 1 AND is_active = 1;
    """)

def create_tag_schema(cursor):
    cursor.executescript("""
    -- Tags table: reusable invoice context labels for reporting and filtering.
    CREATE TABLE IF NOT EXISTS tags (
        id              INTEGER PRIMARY KEY,
        workspace_id    INTEGER,
        name            TEXT    NOT NULL CHECK (length(trim(name)) > 0),
        description     TEXT,
        is_active       INTEGER NOT NULL DEFAULT 1
                                CHECK (is_active IN (0, 1)),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );

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
    cursor.execute("PRAGMA table_info(tags)")
    columns = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if "workspace_id" not in columns:
        cursor.execute("ALTER TABLE tags ADD COLUMN workspace_id INTEGER")

    cursor.execute("DROP INDEX IF EXISTS idx_tags_name_nocase")
    cursor.executescript("""
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_tags_unowned_name_nocase
        ON tags(lower(name))
        WHERE workspace_id IS NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_tags_workspace_name_nocase
        ON tags(workspace_id, lower(name))
        WHERE workspace_id IS NOT NULL;

    CREATE INDEX IF NOT EXISTS
        idx_tags_workspace_id ON tags(workspace_id);
    """)

def create_product_category_schema(cursor):
    cursor.executescript("""
    -- Product categories table: reportable catalog buckets for products.
    CREATE TABLE IF NOT EXISTS product_categories (
        id              INTEGER PRIMARY KEY,
        workspace_id    INTEGER,
        name            TEXT    NOT NULL CHECK (length(trim(name)) > 0),
        description     TEXT,
        is_active       INTEGER NOT NULL DEFAULT 1
                                CHECK (is_active IN (0, 1)),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS
        idx_product_categories_is_active ON product_categories(is_active);

    """)
    cursor.execute("PRAGMA table_info(product_categories)")
    columns = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if "workspace_id" not in columns:
        cursor.execute("ALTER TABLE product_categories ADD COLUMN workspace_id INTEGER")

    cursor.execute("""
        INSERT OR IGNORE INTO product_categories (id, workspace_id, name, description, is_active)
        VALUES (1, NULL, 'Uncategorized', 'Default category for uncategorized products.', 1)
    """)

    cursor.execute("DROP INDEX IF EXISTS idx_product_categories_name_nocase")
    cursor.executescript("""
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_product_categories_unowned_name_nocase
        ON product_categories(lower(name))
        WHERE workspace_id IS NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_product_categories_workspace_name_nocase
        ON product_categories(workspace_id, lower(name))
        WHERE workspace_id IS NOT NULL;

    CREATE INDEX IF NOT EXISTS
        idx_product_categories_workspace_id ON product_categories(workspace_id);
    """)

def create_product_schema(cursor):
    cursor.executescript("""
    -- Products table: reusable catalog items that can later be attached to invoice line items.
    CREATE TABLE IF NOT EXISTS products (
        id              INTEGER PRIMARY KEY,
        workspace_id    INTEGER,
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
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
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
    if "workspace_id" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN workspace_id INTEGER")
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
    cursor.executescript("""
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_products_unowned_name_nocase
        ON products(lower(name))
        WHERE workspace_id IS NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_products_workspace_name_nocase
        ON products(workspace_id, lower(name))
        WHERE workspace_id IS NOT NULL;

    CREATE INDEX IF NOT EXISTS
        idx_products_workspace_id ON products(workspace_id);
    """)

def create_supplier_schema(cursor):
    cursor.executescript("""
    -- Suppliers table: optional product source labels for catalog sourcing.
    CREATE TABLE IF NOT EXISTS suppliers (
        id              INTEGER PRIMARY KEY,
        workspace_id    INTEGER,
        name            TEXT    NOT NULL CHECK (length(trim(name)) > 0),
        phone           TEXT,
        email           TEXT,
        website         TEXT,
        is_active       INTEGER NOT NULL DEFAULT 1
                                CHECK (is_active IN (0, 1)),
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS
        idx_suppliers_is_active ON suppliers(is_active);
    """)
    cursor.execute("PRAGMA table_info(suppliers)")
    columns = {row["name"] if hasattr(row, "keys") else row[1] for row in cursor.fetchall()}
    if "workspace_id" not in columns:
        cursor.execute("ALTER TABLE suppliers ADD COLUMN workspace_id INTEGER")

    cursor.execute("DROP INDEX IF EXISTS idx_suppliers_name_nocase")
    cursor.executescript("""
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_suppliers_unowned_name_nocase
        ON suppliers(lower(name))
        WHERE workspace_id IS NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_suppliers_workspace_name_nocase
        ON suppliers(workspace_id, lower(name))
        WHERE workspace_id IS NOT NULL;

    CREATE INDEX IF NOT EXISTS
        idx_suppliers_workspace_id ON suppliers(workspace_id);
    """)


def create_supplier_location_schema(cursor):
    cursor.executescript("""
    -- Supplier locations table: links suppliers to reusable physical addresses.
    CREATE TABLE IF NOT EXISTS supplier_locations (
        id              INTEGER PRIMARY KEY,
        supplier_id     INTEGER NOT NULL,
        location_id     INTEGER NOT NULL,
        label           TEXT    NOT NULL CHECK (length(trim(label)) > 0),
        is_primary      INTEGER NOT NULL DEFAULT 0
                                CHECK (is_primary IN (0, 1)),
        is_active       INTEGER NOT NULL DEFAULT 1
                                CHECK (is_active IN (0, 1)),
        notes           TEXT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE,
        FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE RESTRICT
    );

    CREATE INDEX IF NOT EXISTS
        idx_supplier_locations_supplier_id ON supplier_locations(supplier_id);
    CREATE INDEX IF NOT EXISTS
        idx_supplier_locations_location_id ON supplier_locations(location_id);
    CREATE INDEX IF NOT EXISTS
        idx_supplier_locations_is_active ON supplier_locations(is_active);
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_supplier_locations_supplier_location
        ON supplier_locations(supplier_id, location_id);
    CREATE UNIQUE INDEX IF NOT EXISTS
        idx_supplier_locations_one_primary
        ON supplier_locations(supplier_id)
        WHERE is_primary = 1 AND is_active = 1;
    """)


def create_product_supplier_schema(cursor):
    cursor.executescript("""
    -- Product suppliers table: many-to-many product source assignments.
    CREATE TABLE IF NOT EXISTS product_suppliers (
        product_id      INTEGER NOT NULL,
        supplier_id     INTEGER NOT NULL,
        note            TEXT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        PRIMARY KEY (product_id, supplier_id),
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE RESTRICT
    );

    CREATE INDEX IF NOT EXISTS
        idx_product_suppliers_product_id ON product_suppliers(product_id);
    CREATE INDEX IF NOT EXISTS
        idx_product_suppliers_supplier_id ON product_suppliers(supplier_id);
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
        c.phone,
        c.customer_type,
        c.company_name,
        c.is_active,
        COUNT(i.id) AS invoice_count,
        COALESCE(SUM(i.total), 0) AS total_cents
    FROM 
        customers c
    LEFT JOIN 
        invoices i ON i.customer_id = c.id
    GROUP BY 
        c.id, c.name, c.email, c.phone, c.customer_type, c.company_name, c.is_active;
    """)

def create_schema(cursor):
    create_workspace_schema(cursor)
    create_business_profile_schema(cursor)
    create_customer_schema(cursor)
    create_location_schema(cursor)
    create_customer_location_schema(cursor)
    create_invoice_schema(cursor)
    create_tag_schema(cursor)
    create_product_category_schema(cursor)
    create_product_schema(cursor)
    create_supplier_schema(cursor)
    create_supplier_location_schema(cursor)
    create_product_supplier_schema(cursor)
    create_invoice_item_schema(cursor)
    create_payment_schema(cursor)
    create_customer_summary_view(cursor)
    create_triggers(cursor)
