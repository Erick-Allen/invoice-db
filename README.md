# invoice-db

A **relational database, CLI, and API application** built with **Python** and **SQLite** for managing customers and invoices.

The project emphasizes practical backend design: normalized relational schema design, business-rule validation, command-line workflows, HTTP API endpoints, query filtering/sorting, and automated test coverage.

## Features

As of **v0.7.0**, the project includes support for: 

- Customer and invoice management
- Full CRUD operations for customers and invoices
- Invoice lifecycle/status management
- Filtering, sorting, and improved invoice queries
- Typer-based CLI with Rich terminal output
- Django REST Framework API Layer
- Shared service layer used by both CLI and API
- Dockerized runtime with persistent storage
- Automated tests with `pytest`

## Architecture

```text
CLI        → services → db
API/DRF    → services → db
future UI  → API → services → db
```

For the full folder breakdown, see [`invoice_db/docs/PROJECT_STRUCTURE.md`](invoice_db/docs/PROJECT_STRUCTURE.md).

## Tech Stack
- SQLite 3
- Python 3
- Typer
- Rich
- Django REST Framework
- Docker
- pytest
- uv

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

## Installation (Docker)

### Clone the repository and build the Docker image locally

```bash
git clone https://github.com/Erick-Allen/invoice-db.git
cd invoice-db
docker build -t invoicedb .
```

### Docker Runner

```bash
./run <command>
```

### Interactive Shell

```bash
docker run --rm -it -v invoicedb_data:/data --entrypoint /bin/sh invoicedb
```

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
- `invoicedb invoices get`
- `invoicedb invoices count`
- `invoicedb invoices update`
- `invoicedb invoices set-status`
- `invoicedb invoices delete`

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
- `POST /api/invoices/`
- `GET /api/invoices/{id}/`
- `PATCH /api/invoices/{id}/`
- `DELETE /api/invoices/{id}/`
- `PATCH /api/invoices/{id}/status/`

## Sample Data & Demo
```bash
uv run python scripts/seed.py
uv run python scripts/demo.py
```

**Note:** `seed.py` seeds the regular project database, while the demo workflow uses a dedicated `demo.sqlite` database in the project root.


## Testing
```bash
uv run pytest --cov=invoice_db --cov-report=term-missing
```

## Version History

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
### [v0.8.0] (Minor)
- Add UI layer

### [v0.9.0] (Minor)
- Add invoice line items

For the full project roadmap, see [`invoice_db/docs/ROADMAP.md`](invoice_db/docs/ROADMAP.md).