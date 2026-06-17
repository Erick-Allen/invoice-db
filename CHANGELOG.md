# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.10.0] - 2026-06-16

### Added

* Added product catalog support across DB, services, CLI, API, and React frontend.
* Added product create, list, get, update, deactivate, and delete workflows.
* Added product API endpoints under `/api/products/`.
* Added product CLI commands under `invoicedb products`.
* Added product frontend page at `/products`.
* Added product test coverage for CLI, API, and frontend behavior.
* Added Docker entrypoint schema initialization for fresh containers.

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
 
### Changed 

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
