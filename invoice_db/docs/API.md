# API Reference

Most app data endpoints require an active session. Users must either sign in or continue as a guest before creating, reading, updating, or deleting workspace data.

## Auth

- `POST /api/auth/signup/`
- `POST /api/auth/login/`
- `POST /api/auth/guest/`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`

## Customers

- `GET /api/customers/`
- `POST /api/customers/`
- `GET /api/customers/{id}/`
- `PATCH /api/customers/{id}/`
- `DELETE /api/customers/{id}/`

## Invoices

- `GET /api/invoices/`
- `GET /api/invoices/?include_items=true`
- `POST /api/invoices/`
- `GET /api/invoices/{id}/`
- `GET /api/invoices/{id}/?include_items=true`
- `PATCH /api/invoices/{id}/`
- `DELETE /api/invoices/{id}/`
- `PATCH /api/invoices/{id}/status/`
- `GET /api/invoices/{id}/items/`
- `POST /api/invoices/{id}/items/`
- `GET /api/invoices/{id}/tags/`
- `POST /api/invoices/{id}/tags/`
- `DELETE /api/invoices/{id}/tags/{tag_id}/`

## Invoice Items

- `GET /api/invoice-items/{id}/`
- `PATCH /api/invoice-items/{id}/`
- `DELETE /api/invoice-items/{id}/`

## Payments

- `GET /api/invoices/{id}/payments/`
- `POST /api/invoices/{id}/payments/`
- `GET /api/invoices/{id}/payments/summary/`
- `GET /api/payments/{id}/`
- `DELETE /api/payments/{id}/`

## Products

- `GET /api/products/`
- `GET /api/products/?active_only=true`
- `POST /api/products/`
- `GET /api/products/{id}/`
- `PATCH /api/products/{id}/`
- `DELETE /api/products/{id}/`
- `PATCH /api/products/{id}/deactivate/`
- `GET /api/products/{id}/suppliers/`
- `POST /api/products/{id}/suppliers/`
- `PATCH /api/products/{id}/suppliers/{supplier_id}/`
- `DELETE /api/products/{id}/suppliers/{supplier_id}/`

## Product Categories

- `GET /api/product-categories/`
- `POST /api/product-categories/`
- `PATCH /api/product-categories/{id}/`
- `DELETE /api/product-categories/{id}/`
- `PATCH /api/product-categories/{id}/deactivate/`

## Tags

- `GET /api/tags/`
- `GET /api/tags/?active_only=true`
- `POST /api/tags/`
- `GET /api/tags/{id}/`
- `PATCH /api/tags/{id}/`
- `DELETE /api/tags/{id}/`
- `PATCH /api/tags/{id}/deactivate/`

## Suppliers

- `GET /api/suppliers/`
- `GET /api/suppliers/?active_only=true`
- `POST /api/suppliers/`
- `GET /api/suppliers/{id}/`
- `PATCH /api/suppliers/{id}/`
- `DELETE /api/suppliers/{id}/`
- `PATCH /api/suppliers/{id}/deactivate/`
- `GET /api/suppliers/{id}/products/`
- `POST /api/suppliers/{id}/remove-from-products/`

## Reports

- `GET /api/reports/overview/`
- `GET /api/reports/overview/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

## Assistant

- `POST /api/assistant/query/`
