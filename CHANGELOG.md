# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.16.0] - 2026-08-17

### Added

* Product costs and invoice item cost snapshots across DB, services, CLI, API, and React frontend.
* Invoice profit calculations with internal cost, profit, and line item controls.
* Reporting foundation with revenue, outstanding due, cost, profit, status, and tag performance views.

## [0.15.0] - 2026-08-17

### Added

* Invoice tags across DB, services, CLI, API, and React frontend.
* Tag management under invoices with create, edit, deactivate, and delete workflows.
* Invoice detail tag assignment.

## [0.14.0] - 2026-08-16

### Added

* Product categories across DB, services, CLI, API, and React frontend.
* Catalog category management with create, edit, deactivate, delete, and product filtering.
* Draft invoice detail workflow for adding line items from the product catalog.

## [0.13.0] - 2026-08-14

### Added

* Customer detail preview with invoice summary, and recent invoice activity.
* Invoice detail preview page with customer context, invoice status, totals, line items, and payment summary.
* Customer-facing printable invoice view.

### Changed

* Refined the product catalog UI with richer product cards and clearer product status and price presentation.

## [0.12.0] - 2026-06-18

### Added

* Payment support across DB, services, CLI, API, and React frontend.
* Payment records, shared payment methods, and payment summaries.
* Sent-only payment creation, overpayment protection, and paid-to-sent reopening on payment deletion.
* Payment CLI commands, API endpoints, frontend payment history, and Pay Balance action.

### Changed

* Manual invoice status changes no longer mark invoices paid; payment create/delete workflows control paid/sent transitions.

## [0.11.0] - 2026-06-17

### Added

* Invoice line items across DB, services, CLI, API, and React frontend.
* Product-backed line items with quantity, price snapshots, calculated totals, and locked sent/paid/void edits.
* Invoice item CLI/API endpoints, `include_items=true`, and `invoicedb invoices list --include-items`.
* Frontend line-item workflows and test coverage.

### Changed

* Invoice totals are calculated from line items instead of manual invoice total inputs.
* Improved frontend invoice loading and status-change error messages.

## [0.10.0] - 2026-06-16

### Added

* Product catalog support across DB, services, CLI, API, and React frontend.
* Product create, list, get, update, deactivate, and delete workflows.
* Product test coverage for CLI, API, and frontend behavior.
* Docker entrypoint schema initialization for fresh containers.

### Changed

* Updated Docker startup so the SQLite schema is initialized automatically before the API starts.

## [0.9.0] - 2026-06-09

### Added

* Added a guarded natural-language invoice assistant.
* Added intent classification for supported invoice queries.
* Added Pydantic validation for assistant intent contracts.
* Added an assistant dispatcher that routes validated intents through the service layer only.
* Added optional local Qwen/Ollama fallback for ambiguous assistant requests.
* Added the `POST /api/assistant/query/` endpoint.
* Added React invoice assistant UI with suggested prompts.
* Added assistant result rendering for invoice counts and invoice lists.
* Added dashboard summary cards for customers, invoices, and invoice statuses.
* Added recent customer and recent invoice dashboard panels.

### Changed

* Updated Docker runtime to start the Django API by default.
* Polished React navigation, dashboard, customers, and invoices pages.
* Improved customer and invoice tables by hiding raw database IDs from users.
* Updated invoice display to show customer names instead of raw customer IDs.
* Updated project Python requirement to Python 3.11+.
* Pinned `scikit-learn` to match the trained classifier artifact.
## [0.8.0] - 2026-05-27

### Added
- React + TypeScript frontend built with Vite
- Dashboard, customer, and invoice UI pages
- Customer create, edit, delete, and list workflows
- Invoice create, edit, delete, list, and status update workflows
- Frontend API client for customer and invoice endpoints
- Frontend tests with Vitest and React Testing Library

### Changed
- Standardized invoice totals as integer cents across the API, service layer, and database layer
- Updated CLI total handling so user-entered dollar amounts are converted to cents before reaching services
- Updated backend tests to reflect cents-based invoice total handling

## [0.7.0] - 2026-05-11

### Added
- Shared service layer for customers and invoices
- Django REST Framework API layer
- Customer and invoice API endpoints
- API tests for customer and invoice endpoints

### Changed
- Modify cli tests to reflect service-layer archtiecture 

## [0.6.0] - 2026-04-14

### Added
- Invoice status support (`draft`, `sent`, `paid`, `void`)
- Overdue invoice querying
- `uv.lock`
- `CONTRIBUTING.md`

### Changed
- Improve invoice list filtering and sorting
- Update invoice count filtering
- Renamed invoice primary key from `invoice_id` to `id`
- Updated invoice check constraints
