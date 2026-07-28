# PRD — Fujitec Service Inspection Report (SIR) App

## Original Problem Statement
Web + mobile app for elevator (lift) unit inspection by technicians at jobsites (PT Fujitec Indonesia). Technicians fill a Service Inspection Report: header info (job number, site name, date, time from/to, technician, total units, unit/lift number), select checklist type (1M / 3M / 12M), complete the dynamic checklist with judgment marks (✔ Good, ◎ Replaced/Adjusted, ✖ Damage, ▬ None), per-item remarks, measurements + photos for specified checkpoints, a global remark, spare-part requirements, and 4 digital signatures. Data is stored centrally as historical records. A follow-up dashboard tracks spare-part replacement movement across Sales, Customer (PO), Inventory, and Maintenance teams. PDF export of the report is required.

## Architecture
- **Backend**: FastAPI + MongoDB (motor). JWT auth (Bearer). Object storage via Emergent for photos. reportlab for PDF.
- **Frontend**: React 19 + React Router + Tailwind + shadcn/ui + Phosphor icons + recharts. Mobile-first (bottom nav) + desktop sidebar.
- **Master checklist**: `checklist_data.py` — 54 items across 6 sections (Elevator Operation, Motor Room, Car, Hoistway, Pit, Others), each with 1M/3M/12M applicability and photo_points count (items 10,45,47,48,49,50,51 require measurement+photo).

## Roles
admin, technician, supervisor, head_maintenance, sales, inventory, customer. Seeded on startup (see /app/memory/test_credentials.md).

## Implemented (2026-07-28)
- JWT auth (login/register/me), 7 seeded demo accounts, brute-force lockout.
- Dynamic checklist master API filtered by 1M/3M/12M with photo_points.
- New Inspection 4-step wizard: header → checklist (section tabs, judgment toggles, measurement+photo per point, remarks) → global remark + spare parts → 4 signature pads → submit/draft.
- Photo upload to object storage + retrieval.
- Inspection history (search/filter), detail view with results, measurements, photos, signatures.
- Status workflow: draft → submitted → checked (supervisor) → approved (head maintenance), role-gated.
- Spare-part follow-up: embedded per inspection + aggregated `/spare-parts` dashboard with per-team status (Sales/Customer PO/Inventory/Maintenance), role-based edit authorization, filters.
- Dashboard with stats + inventory breakdown chart + recent inspections.
- PDF export of SIR report.
- Admin user management.
- Verified: testing agent 100% backend (30/30) + 100% frontend E2E.

## Backlog / Next
- P1: Google login (user also selected this alongside JWT) — add Emergent Google auth.
- P1: PDF should embed inspection photos (currently lists measurements/marks/signatures only).
- P2: Scope customer role to their own site(s); site master data / job-number lookup.
- P2: Notifications when spare-part follow-up status changes; export history to Excel.
- P2: Pagination on lists; login rate-limit key via X-Forwarded-For.
