# invoice-db
A relational database, CLI, API, React UI, and AI assistant application built with Python, SQLite, and TypeScript for managing customers, invoices, and products.

The project emphasizes practical full-stack design: normalized relational schema design, shared service-layer business logic, command-line workflows, HTTP API endpoints, React-based UI workflows, Dockerized runtime support, natural-language invoice querying, and automated test coverage.

## Features
As of **v0.16.0**, the project includes support for:

- Customer, invoice, invoice tag, product, product category, line-item, and payment workflows
- Derived invoice totals, payment summaries, cost snapshots, profit calculations, and invoice status rules
- Customer and invoice detail previews with printable invoice output
- Product catalog browsing, category filtering, and catalog-driven invoice item selection
- Invoice tagging for job/context reporting
- Reporting foundation for revenue, outstanding due, cost, profit, status, and tag performance
- Typer CLI, Django REST API, and React + TypeScript frontend
- Shared service layer used by CLI and API
- Guarded natural-language invoice assistant
- Dockerized backend runtime with persistent SQLite storage
- Backend and frontend test coverage

## Architecture

```text
CLI        → services → db
API/DRF    → services → db
React UI   → API → services → db
Assistant  → router/classifier → validated intent → dispatcher → services → db
Qwen fallback → validated intent/message only
```

For the full folder breakdown, see [`invoice_db/docs/PROJECT_STRUCTURE.md`](invoice_db/docs/PROJECT_STRUCTURE.md).

## Tech Stack
- Python 3
- SQLite 3
- Typer
- Rich
- Django REST Framework
- React
- TypeScript
- Vite
- Vitest
- React Testing Library
- Docker
- pytest
- scikit-learn
- Pydantic
- uv
- Optional: Ollama/Qwen for assistant fallback

## Installation (Local)

### 1. Install `uv`
Install `uv` first if you do not already have it installed.

### 2. Clone the repository
```bash
git clone https://github.com/Erick-Allen/invoice-db.git
cd invoice-db
```
### 3. Sync the project environment
```bash
uv sync --extra dev
```
### 4. Run the CLI
```bash
uv run invoicedb --help
```

### 5. Run the API server
```bash
uv run python manage.py runserver
```

### 6. Install frontend dependencies
```bash
cd frontend
npm install
```

### 7. Run React UI
```bash
npm run dev
```

## Installation (Docker)

### Clone the repository and build the Docker image locally

```bash
git clone https://github.com/Erick-Allen/invoice-db.git
cd invoice-db
docker build -t invoicedb .
```

### Run the Dockerized backend API

```bash
docker run --rm -p 8000:8000 -v ${PWD}/data:/data invoicedb
```

The Docker entrypoint creates `/data` if needed and initializes the SQLite schema automatically before starting the API. Mount `/data` to persist the database between container runs.

### Interactive Shell

```bash
docker run --rm -it -v invoicedb_data:/data --entrypoint /bin/sh invoicedb
```

### Docker and Qwen/Ollama fallback

If the Dockerized backend needs to reach Ollama running on the host machine, localhost:11434 will not work from 

Use:

```bash
http://host.docker.internal:11434/api/chat
```

The default local fallback model is:

qwen3:0.6b

## CLI Usage

### Database commands
- `invoicedb db init`
- `invoicedb db drop`
- `invoicedb db delete`

### Customer commands
- `invoicedb customers create`
- `invoicedb customers list`
- `invoicedb customers get`
- `invoicedb customers update`
- `invoicedb customers delete`

### Invoice commands
- `invoicedb invoices create`
- `invoicedb invoices list`
- `invoicedb invoices list --include-items`
- `invoicedb invoices get`
- `invoicedb invoices tags`
- `invoicedb invoices add-tag`
- `invoicedb invoices remove-tag`
- `invoicedb invoices count`
- `invoicedb invoices update`
- `invoicedb invoices set-status`
- `invoicedb invoices delete`

### Invoice item commands
- `invoicedb invoice-items add`
- `invoicedb invoice-items list`
- `invoicedb invoice-items get`
- `invoicedb invoice-items update`
- `invoicedb invoice-items delete`

### Payment commands
- `invoicedb payments add`
- `invoicedb payments list`
- `invoicedb payments get`
- `invoicedb payments summary`
- `invoicedb payments delete`

### Product commands
- `invoicedb products add`
- `invoicedb products list`
- `invoicedb products get`
- `invoicedb products update`
- `invoicedb products deactivate`
- `invoicedb products delete`

### Product category commands
- `invoicedb product-categories add`
- `invoicedb product-categories list`
- `invoicedb product-categories update`
- `invoicedb product-categories deactivate`
- `invoicedb product-categories delete`

### Tag commands
- `invoicedb tags add`
- `invoicedb tags list`
- `invoicedb tags get`
- `invoicedb tags update`
- `invoicedb tags deactivate`
- `invoicedb tags delete`

### Assistant command
- `invoicedb assistant ask`
- `invoicedb assistant ask --use-qwen`

**Other**
- `invoicedb --version`

## API Endpoints

### Customers
- `GET /api/customers/`
- `POST /api/customers/`
- `GET /api/customers/{id}/`
- `PATCH /api/customers/{id}/`
- `DELETE /api/customers/{id}/`

### Invoices
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

### Invoice Items
- `GET /api/invoice-items/{id}/`
- `PATCH /api/invoice-items/{id}/`
- `DELETE /api/invoice-items/{id}/`

### Payments
- `GET /api/invoices/{id}/payments/`
- `POST /api/invoices/{id}/payments/`
- `GET /api/invoices/{id}/payments/summary/`
- `GET /api/payments/{id}/`
- `DELETE /api/payments/{id}/`

### Products
- `GET /api/products/`
- `GET /api/products/?active_only=true`
- `POST /api/products/`
- `GET /api/products/{id}/`
- `PATCH /api/products/{id}/`
- `DELETE /api/products/{id}/`
- `PATCH /api/products/{id}/deactivate/`

### Product Categories
- `GET /api/product-categories/`
- `POST /api/product-categories/`
- `PATCH /api/product-categories/{id}/`
- `DELETE /api/product-categories/{id}/`
- `PATCH /api/product-categories/{id}/deactivate/`

### Tags
- `GET /api/tags/`
- `GET /api/tags/?active_only=true`
- `POST /api/tags/`
- `GET /api/tags/{id}/`
- `PATCH /api/tags/{id}/`
- `DELETE /api/tags/{id}/`
- `PATCH /api/tags/{id}/deactivate/`

### Reports
- `GET /api/reports/overview/`
- `GET /api/reports/overview/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

### Assistant

- `POST /api/assistant/query/`

## Sample Data & Demo (CLI)
```bash
uv run python scripts/seed.py
uv run python scripts/demo.py
```

**Note:** `seed.py` seeds the regular project database, while the demo workflow uses a dedicated `demo.sqlite` database in the project root.


## Testing

### Backend tests
```bash
uv run pytest --cov=invoice_db --cov-report=term-missing
```

### Frontend tests
```bash
cd frontend
npm run test:run
```

## Version History

### [v0.16.0]
#### Added
- Product costs and invoice item cost snapshots across DB, services, CLI, API, and React frontend
- Invoice profit calculations and internal line item controls
- Reporting foundation with revenue, outstanding due, cost, profit, status, and tag performance

### [v0.15.0]
#### Added
- Invoice tags across DB, services, CLI, API, and React frontend
- Tag management under invoices with create, edit, deactivate, and delete workflows
- Invoice detail tag assignment for existing active tags

### [v0.14.0]
#### Added
- Product categories across DB, services, CLI, API, and React frontend
- Catalog category management, deletion rules, and product filtering
- Invoice creation and draft invoice detail item adding from catalog products

#### Changed
- Improved duplicate product category errors with clearer messages
- Simplified invoice lists to show item counts instead of inline item/payment controls
- Moved create workflows into modal forms

### [v0.13.0]
#### Added
- Customer detail preview page with customer profile, invoice summary, and recent invoice activity
- Invoice detail preview page with customer context, invoice status, totals, line items, and payment summary
- Customer-facing printable invoice view

#### Changed
- Refined product catalog UI with richer product cards and clearer product status/price presentation

### [v0.12.0]
#### Added
- Payments across DB, services, CLI, API, and React frontend
- Partial/full payment tracking with payment summaries
- Sent-only payment creation, overpayment protection, and paid-to-sent reopening on payment deletion
- `invoicedb payments add/list/get/summary/delete`
- Payment API endpoints and frontend Pay Balance action

#### Changed
- Manual status changes no longer mark invoices paid; payments control sent/paid transitions.

### [v0.11.0]
#### Added
- Invoice line items across DB, services, CLI, API, and React frontend
- Product-backed line items with price snapshots and locked sent/paid/void edits
- `include_items=true`, `invoicedb invoice-items`, and `invoicedb invoices list --include-items`
- Inactive-product checks before adding/replacing line items or sending invoices

#### Changed
- Invoice totals are calculated from line items instead of manual invoice total inputs.
- Invoice frontend now shows clearer load and status-change errors.

### [v0.10.0]
#### Added
- Product catalog table and DB helpers
- Product service layer
- Product CLI commands
- Product API endpoints
- React product catalog page
- Product tests across CLI, API, and frontend
- Docker entrypoint that initializes the SQLite schema automatically

### [v0.9.0]
#### Added
- Natural-language invoice assistant
- Intent classifier for supported invoice queries

#### Changed
- Updated Docker runtime from CLI-first behavior to API server behavior

### [v0.8.0]
#### Added
- React + TypeScript frontend built with Vite
- Frontend pages for dashboard, customers, and invoices
- Customer create, edit, delete, and list workflows
- Invoice create, edit, delete, list, and status update workflows
- Frontend API client for customer and invoice endpoints
- Frontend tests with Vitest and React Testing Library

#### Changed
- Standardized invoice totals as integer cents across the API, service layer, and database

### [v0.7.0]
#### Added
- Shared service layer for customers and invoices
- Django REST Framework API Layer
- Customer API endpoints
- Invoice API endpoints
- API test coverage for customer and invoice endpoints

#### Changed
- Updated CLI commands to use the shared service layer

### [v0.6.0]
#### Added
- Invoice lifecycle/status logic
- Overdue invoice querying

#### Changed
- Improved invoice list and count querying

### [v0.5.0]
#### Added
- Rich-based terminal output
- Packaged CLI as a global console command (`invoicedb`)
- Docker support
- Demo automation scripts

### [v0.4.0]
#### Added
- Full invoice CRUD support in the CLI

### [v0.3.0]
#### Added
- Introduced Typer-based CLI for customer and database management

### [v0.2.0]
#### Added
- Added customer and invoice test coverage

### [v0.1.0]
#### Added
- Initial SQLite schema and core CRUD functionality

## Roadmap
### [v0.17.0] (Planned)
- Product suppliers

### [v0.18.0] (Planned)
- Customer record improvements

For the full project roadmap, see [`invoice_db/docs/ROADMAP.md`](invoice_db/docs/ROADMAP.md).
