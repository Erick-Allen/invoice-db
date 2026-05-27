# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.8.0] - 2026-##-##

### Added
- UI for dashboard, customer, invoices

### Changed
- Stopped db and from converting input to cents. Refactor test to reflect the new change
- CLI now converts totals to cents before passing values


## [0.7.0] - 2026-03-06

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