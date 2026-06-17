invoice-db/
|-- api/                         # Django REST Framework API app
|   |-- migrations/
|   |-- serializers.py
|   |-- urls.py
|   `-- views.py
|
|-- frontend/                    # React + TypeScript frontend UI
|   |-- src/
|   |   |-- api/                 # Frontend API client modules
|   |   |   |-- client.ts
|   |   |   |-- customers.ts
|   |   |   |-- invoiceItems.ts
|   |   |   |-- invoices.ts
|   |   |   `-- products.ts
|   |   |
|   |   |-- pages/               # Page-level React components
|   |   |   |-- CustomersPage.tsx
|   |   |   |-- DashboardPage.tsx
|   |   |   |-- InvoicesPage.tsx
|   |   |   `-- ProductsPage.tsx
|   |   |
|   |   |-- test/                # Frontend test setup and UI tests
|   |   |   |-- setup.ts
|   |   |   |-- App.test.tsx
|   |   |   |-- CustomersPage.test.tsx
|   |   |   |-- InvoicesPage.test.tsx
|   |   |   |-- ProductsPage.test.tsx
|   |   |   `-- money.test.ts
|   |   |
|   |   |-- utils/
|   |   |   `-- money.ts
|   |   |
|   |   |-- App.css
|   |   |-- App.tsx
|   |   |-- index.css
|   |   `-- main.tsx
|   |
|   |-- eslint.config.js
|   |-- index.html
|   |-- package-lock.json
|   |-- package.json
|   |-- tsconfig.app.json
|   |-- tsconfig.json
|   |-- tsconfig.node.json
|   `-- vite.config.ts
|
|-- invoice_db/                  # Main Python application package
|   |-- assistant/               # Natural-language assistant
|   |-- cli/                     # Typer CLI layer
|   |   |-- app.py
|   |   |-- customers_cmds.py
|   |   |-- db_cmds.py
|   |   |-- invoice_items_cmds.py
|   |   |-- invoices_cmds.py
|   |   |-- products_cmds.py
|   |   |-- render_customers.py
|   |   |-- render_invoice_items.py
|   |   |-- render_invoices.py
|   |   |-- render_products.py
|   |   `-- ui.py
|   |
|   |-- db/                      # SQLite database layer
|   |   |-- connection.py
|   |   |-- customers.py
|   |   |-- invoice_items.py
|   |   |-- invoices.py
|   |   |-- products.py
|   |   |-- schema.py
|   |   `-- validators.py
|   |
|   |-- docs/
|   |   |-- PROJECT_STRUCTURE.md
|   |   |-- ROADMAP.md
|   |   `-- ERDdiagram-Roadmap.png
|   |
|   |-- services/                # Shared business logic for CLI and API
|   |   |-- customers.py
|   |   |-- exceptions.py
|   |   |-- invoice_items.py
|   |   |-- invoices.py
|   |   `-- products.py
|   |
|   |-- __main__.py
|   `-- utils.py
|
|-- server/                      # Django project configuration
|   |-- asgi.py
|   |-- settings.py
|   |-- urls.py
|   `-- wsgi.py
|
|-- tests/                       # Backend automated test suite
|   |-- api/
|   |   |-- conftest.py
|   |   |-- test_customers_api.py
|   |   |-- test_invoice_items_api.py
|   |   |-- test_invoices_api.py
|   |   `-- test_products_api.py
|   |
|   |-- cli/
|   |   |-- conftest.py
|   |   |-- test_cli_customers.py
|   |   |-- test_cli_general.py
|   |   |-- test_cli_invoice_items.py
|   |   |-- test_cli_invoices.py
|   |   `-- test_cli_products.py
|   |
|   |-- assistant/
|   |-- db/
|   |   |-- test_invoice_items_repository.py
|   |   |-- test_invoice_items_schema.py
|   |   |-- test_product_validation.py
|   |   `-- test_products_crud.py
|   |
|   `-- services/
|       |-- test_invoice_items_service.py
|       `-- test_invoices_service.py
|
|-- scripts/
|   |-- demo.py
|   `-- seed.py
|
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- Dockerfile
|-- docker_entrypoint.py
|-- manage.py
|-- pyproject.toml
|-- README.md
`-- uv.lock
