# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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