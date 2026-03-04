# invoice-db

A relational database project built with **SQLite** and **Python**. It manages customers and their invoices with full **CRUD operations** through a **Command Line Interface (CLI)**.

As of **v0.5.1**, the **CLI** includes support for: 
- Database initialization, reset, and deletion
- customer management
- Invoice management
- Rich terminal output
- Dockerized runtime with persistent storage

The CLI is built with [Typer](https://typer.tiangolo.com/)

### Built With
- SQLite 3
- Python 3
- Typer
- Rich
- Docker

---

# Installation (Local)

### Clone the repository and install dependencies:

```bash
git clone https://github.com/Erick-Allen/customer-invoice-db.git
cd invoice-db
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Verify installation:
 
```bash
invoicedb --help
```

# Installation (Docker)

### Clone the repository and build the Docker image locally:

```bash
git clone https://github.com/Erick-Allen/customer-invoice-db.git
cd customer-invoice-db
docker build -t invoicedb .
```

### Docker Runner:

```bash
./run <command>
```

### Interactive Shell:

```bash
docker run --rm -it -v invoicedb_data:/data --entrypoint /bin/sh invoicedb
```

# Usage

**Database commands**

- `invoicedb db init`
- `invoicedb db drop`
- `invoicedb db delete`

**customer commands**
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
- `invoicedb invoices delete`

**Other**
- `invoicedb --version`

# Demo & Development Scripts

The 'scripts/' folder contains helper scripts for:
- Resetting the database
- Seeding demo customers and invoices
- Running a full demo workflow

The demo workflow runs against a dedicated `demo.sqlite` database in the project root and does not affect normal customer data.

# Version History
## [v0.5.0]
### Added
- Rich-based terminal output
- Packaged CLI as a global console command (`invoicedb`)
- Docker support
- Demo automation scripts

## [v0.4.0]
### Added
- Full invoice CRUD support in the CLI

## [v0.3.0]
### Added
- Introduced Typer-based CLI for customer and database management

## [v0.1.0]
### Added
- Initial SQLite schema and core CRUD functionality

# Roadmap

## [v0.6.0] (Minor)
- Invoice state, filtering and sorting
- Query usability improvements

## [v0.7.0] (Minor)
- Reporting and analytics commands