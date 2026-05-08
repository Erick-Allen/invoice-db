# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

## [0.7.0] - 2026-##-##

### Added
- Service layer for customers and invoices
- Converted from db sqlite.row to dictionaries in services  

### Changed
- Modify cli tests to service changes

### Considerations
- Convert data from dict to dataclass or pydantic model
- Look at and maybe seperate tests where id is 9999
because -9999 is a validationerror and 9999 is notfounderror

### Need to Change
- create database services for create, drop, delete