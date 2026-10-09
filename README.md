# invoice-db
A relational database, Django API, React UI, AI assistant, and legacy local CLI application built with Python, SQLite, and TypeScript for managing customers, invoices, and products.

The project emphasizes practical full-stack design: normalized relational schema design, shared service-layer business logic, HTTP API endpoints, React-based UI workflows, session-based authentication, workspace-scoped data, Dockerized runtime support, natural-language invoice querying, and automated test coverage.

## Features
As of **v0.21.0**, InvoiceDB supports:

- Signed-in and guest workspaces
- Customer, invoice, product, supplier, and payment management
- Draft invoices with services, statuses, profile-aware print views, and customer-facing pages
- Business profile and invoice settings for sender details, payment terms, accepted payment methods, footer notes, and tax defaults
- Workspace-scoped business documents with rich text editing and searchable plain-text extraction
- Invoice subtotal, tax, total, amount paid, balance due, and draft-level tax overrides
- Revenue, balance, cost, profit, status, and tag reporting
- Workspace-scoped assistant queries

The web app and API are the primary product surfaces. The CLI remains available for local development and database inspection.

## Architecture

```text
Legacy CLI → services → db
API/DRF    → session auth → workspace scope → services → db
React UI   → API → session auth → workspace scope → services → db
Assistant  → router/classifier → validated intent → dispatcher → workspace-scoped services → db
Qwen fallback → validated intent/message only
```

For the full folder breakdown, see [`invoice_db/docs/PROJECT_STRUCTURE.md`](invoice_db/docs/PROJECT_STRUCTURE.md).

## Tech Stack
- **Backend:** Python, Django REST Framework, SQLite
- **Frontend:** React, TypeScript, Vite
- **Assistant:** scikit-learn intent routing with optional Ollama/Qwen fallback
- **Tooling:** uv, pytest, Vitest, Docker

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

### 4. Run Django migrations
```bash
uv run python manage.py migrate
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

The Docker entrypoint creates `/data` if needed, initializes the InvoiceDB SQLite schema, runs Django migrations, and starts the API. Mount `/data` to persist both the invoice data and Django auth/session data between container runs.

### Interactive Shell

```bash
docker run --rm -it -v invoicedb_data:/data --entrypoint /bin/sh invoicedb
```

### Docker and Qwen/Ollama fallback

If the Dockerized backend needs to reach Ollama running on the host machine, localhost:11434 will not work from inside the container.

Use:

```bash
docker run --rm -p 8000:8000 -v ${PWD}/data:/data \
  -e INVOICEDB_OLLAMA_CHAT_URL=http://host.docker.internal:11434/api/chat \
  invoicedb
```

The default local fallback model is:

qwen3:0.6b

## CLI Usage

The CLI is retained as legacy/local tooling. Current product development targets the Django API and React frontend. CLI commands may still be useful for local inspection and database workflows, but they are not the primary supported interface going forward.

```bash
uv run invoicedb --help
```

## Guest Workspace Cleanup

Guest workspaces are temporary and may be deleted after 24 hours. Expired guest workspaces and their temporary users can be cleaned up manually with:

```bash
uv run python manage.py cleanup_guest_workspaces
```

## Sample Data & Demo (Legacy CLI)
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

## Project Docs

- API reference: [`invoice_db/docs/API.md`](invoice_db/docs/API.md)
- Changelog: [`CHANGELOG.md`](CHANGELOG.md)
- Roadmap: [`invoice_db/docs/ROADMAP.md`](invoice_db/docs/ROADMAP.md)
- Project structure: [`invoice_db/docs/PROJECT_STRUCTURE.md`](invoice_db/docs/PROJECT_STRUCTURE.md)
