# invoice-db

A **relational database and CLI application** built with **Python** and **SQLite** for managing customers and invoices from the terminal. The project emphasizes practical backend design: normalized relational schema design, business-rule validation, command-line workflows, query filtering/sorting, and automated test coverage.

## Features

As of **v0.6.0**, the **CLI** includes support for: 

- Customer and invoice management from the terminal
- Full CRUD operations for customers and invoices
- Invoice lifecycle/status management
- Filtering, sorting, and improved invoice queries
- Rich terminal output
- Dockerized runtime with persistent storage
- Automated tests with `pytest`

## Tech Stack
- SQLite 3
- Python 3
- Typer
- Rich
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

## Usage

**Database commands**

- `invoicedb db init`
- `invoicedb db drop`
- `invoicedb db delete`

**Customer commands**
- `invoicedb customers create`
- `invoicedb customers list`
- `invoicedb customers get`
- `invoicedb customers update`
- `invoicedb customers delete`

**Invoice commands**
- `invoicedb invoices create`
- `invoicedb invoices list`
- `invoicedb invoices get`
- `invoicedb invoices count`
- `invoicedb invoices update`
- `invoicedb invoices set-status`
- `invoicedb invoices delete`

**Other**
- `invoicedb --version`

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

### [v0.1.0]
#### Added
- Initial SQLite schema and core CRUD functionality


## Roadmap

### [v0.7.0] (Minor)
- Add API layer

### [v0.8.0] (Minor)
- Add UI layer

