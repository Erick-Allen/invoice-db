from dataclasses import dataclass
from sqlite3 import Row

from .invoices import get_invoice_by_id
from .products import get_product_by_id
from .validators import validate_quantity, validate_unit_price_cents


@dataclass
class InvoiceItemCreate:
    invoice_id: int
    product_id: int
    quantity: int = 1
    unit_price_cents: int | None = None


@dataclass
class InvoiceItem:
    id: int
    invoice_id: int
    product_id: int
    quantity: int
    unit_price_cents: int
    created_at: str
    updated_at: str

    @property
    def line_total_cents(self) -> int:
        return self.quantity * self.unit_price_cents


class InvoiceItemRepository:
    def __init__(self, cursor):
        self.cursor = cursor

    def create(self, item: InvoiceItemCreate) -> InvoiceItem:
        self._require_invoice(item.invoice_id)
        product = self._require_active_product(item.product_id)

        quantity = validate_quantity(item.quantity)
        unit_price_cents = (
            product.unit_price_cents
            if item.unit_price_cents is None
            else validate_unit_price_cents(item.unit_price_cents)
        )

        self.cursor.execute("""
            INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price)
            VALUES (?, ?, ?, ?)
        """, (item.invoice_id, item.product_id, quantity, unit_price_cents))

        created_item = self.get_by_id(self.cursor.lastrowid)
        if created_item is None:
            raise RuntimeError("Invoice item was created but could not be retrieved.")

        self.recalculate_invoice_total(item.invoice_id)
        return created_item

    def get_by_id(self, invoice_item_id: int) -> InvoiceItem | None:
        self.cursor.execute("SELECT * FROM invoice_items WHERE id = ?", (invoice_item_id,))
        row = self.cursor.fetchone()
        return self._to_invoice_item(row) if row else None

    def list_by_invoice_id(self, invoice_id: int) -> list[InvoiceItem]:
        self.cursor.execute("""
            SELECT *
            FROM invoice_items
            WHERE invoice_id = ?
            ORDER BY id
        """, (invoice_id,))
        return [self._to_invoice_item(row) for row in self.cursor.fetchall()]

    def update(
        self,
        invoice_item_id: int,
        *,
        product_id: int | None = None,
        quantity: int | None = None,
        unit_price_cents: int | None = None,
    ) -> InvoiceItem | None:
        item = self.get_by_id(invoice_item_id)
        if item is None:
            return None

        updates, params = [], []

        if product_id is not None:
            product = self._require_active_product(product_id)
            updates.append("product_id = ?")
            params.append(product.id)
            if unit_price_cents is None:
                updates.append("unit_price = ?")
                params.append(product.unit_price_cents)
        if quantity is not None:
            updates.append("quantity = ?")
            params.append(validate_quantity(quantity))
        if unit_price_cents is not None:
            updates.append("unit_price = ?")
            params.append(validate_unit_price_cents(unit_price_cents))

        if not updates:
            return item

        params.append(invoice_item_id)
        query = f"UPDATE invoice_items SET {', '.join(updates)} WHERE id = ?"
        self.cursor.execute(query, tuple(params))

        self.recalculate_invoice_total(item.invoice_id)
        return self.get_by_id(invoice_item_id)

    def delete(self, invoice_item_id: int) -> bool:
        item = self.get_by_id(invoice_item_id)
        if item is None:
            return False

        self.cursor.execute("DELETE FROM invoice_items WHERE id = ?", (invoice_item_id,))
        deleted = self.cursor.rowcount > 0

        if deleted:
            self.recalculate_invoice_total(item.invoice_id)

        return deleted

    def sum_invoice_items(self, invoice_id: int) -> int:
        self.cursor.execute("""
            SELECT COALESCE(SUM(quantity * unit_price), 0) AS total
            FROM invoice_items
            WHERE invoice_id = ?
        """, (invoice_id,))
        row = self.cursor.fetchone()
        return row["total"] if row else 0

    def recalculate_invoice_total(self, invoice_id: int) -> int:
        total = self.sum_invoice_items(invoice_id)
        self.cursor.execute(
            "UPDATE invoices SET total = ? WHERE id = ?",
            (total, invoice_id),
        )
        return total

    def _require_invoice(self, invoice_id: int) -> None:
        if get_invoice_by_id(self.cursor, invoice_id) is None:
            raise ValueError(f"Invoice not found (id={invoice_id})")

    def _require_active_product(self, product_id: int):
        product = get_product_by_id(self.cursor, product_id)
        if product is None:
            raise ValueError(f"Product not found (id={product_id})")
        if not product.is_active:
            raise ValueError(f"Product is inactive (id={product_id})")
        return product

    def _to_invoice_item(self, row: Row) -> InvoiceItem:
        return InvoiceItem(
            id=row["id"],
            invoice_id=row["invoice_id"],
            product_id=row["product_id"],
            quantity=row["quantity"],
            unit_price_cents=row["unit_price"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
