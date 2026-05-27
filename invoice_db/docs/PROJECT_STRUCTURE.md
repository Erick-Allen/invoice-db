invoice-db/
├── api/                         # Django REST Framework API app
│   ├── migrations/
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
│
├── frontend/                    # React + TypeScript frontend UI
│   ├── src/
│   │   ├── api/                 # Frontend API client modules
│   │   │   ├── client.ts
│   │   │   ├── customers.ts
│   │   │   └── invoices.ts
│   │   │
│   │   ├── pages/               # Page-level React components
│   │   │   ├── CustomersPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   └── InvoicesPage.tsx
│   │   │
│   │   ├── test/                # Frontend test setup and UI tests
│   │   │   ├── setup.ts
│   │   │   ├── App.test.tsx
│   │   │   ├── CustomersPage.test.tsx
│   │   │   ├── InvoicesPage.test.tsx
│   │   │   └── money.test.ts
│   │   │
│   │   ├── utils/               # Frontend utility helpers
│   │   │   └── money.ts
│   │   │
│   │   ├── App.css
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   │
│   ├── .env.example             # Example frontend environment variables
│   ├── eslint.config.js
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
│
├── invoice_db/                  # Main Python application package
│   ├── cli/                     # Typer CLI layer
│   │   ├── app.py
│   │   ├── customers_cmds.py
│   │   ├── invoices_cmds.py
│   │   ├── db_cmds.py
│   │   ├── render_customers.py
│   │   ├── render_invoices.py
│   │   └── ui.py
│   │
│   ├── db/                      # SQLite database layer
│   │   ├── connection.py
│   │   ├── customers.py
│   │   ├── invoices.py
│   │   ├── schema.py
│   │   └── validators.py
│   │
│   ├── docs/                    # Project documentation and diagrams
│   │   ├── PROJECT_STRUCTURE.md
│   │   ├── ROADMAP.md
│   │   └── ERDDiagram-Roadmap.png
│   │
│   ├── services/                # Shared business logic for CLI and API
│   │   ├── customers.py
│   │   ├── exceptions.py
│   │   └── invoices.py
│   │
│   ├── __main__.py
│   └── utils.py
│
├── server/                      # Django project configuration
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── tests/                       # Backend automated test suite
│   ├── api/
│   │   ├── conftest.py
│   │   ├── test_customers_api.py
│   │   └── test_invoices_api.py
│   │
│   ├── cli/
│   │   ├── conftest.py
│   │   ├── test_cli_customers.py
│   │   ├── test_cli_general.py
│   │   └── test_cli_invoices.py
│   │
│   └── db/
│       ├── test_customer_validation.py
│       ├── test_customers_crud.py
│       ├── test_invoice_queries.py
│       ├── test_invoice_validation.py
│       └── test_invoices_crud.py
│
├── scripts/
│   ├── demo.py
│   ├── demo.sqlite
│   └── seed.py
│
├── docs/
│   └── ERDDiagram-Roadmap.png
│
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile
├── manage.py
├── pyproject.toml
├── README.md
└── uv.lock