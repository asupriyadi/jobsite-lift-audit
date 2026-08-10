# PRD — Fujitec Service Inspection Report (SIR) App

## Original Problem Statement
Web + mobile app for elevator inspection at jobsites (PT Fujitec Indonesia). Technicians fill Service Inspection Reports (SIR) with header info, checklist type (1M/3M/12M), judgment marks, per-checkpoint measurements + photos, spare-part requirements, and digital signatures. Central historical DB. Spare-part follow-up dashboard across Sales/Customer(PO)/Inventory/Maintenance teams. PDF export. Iterations added: Google login, building master autofill, draft editing, 100% submit gating, email notifications, standardized PDF filenames + logo watermark, supervisor/head signatures & status downgrade, and two new report types (ECR Call Back, HOR Hand Over).

## Architecture
- Backend: FastAPI + MongoDB (motor). JWT auth (Bearer) + Emergent Google OAuth. Object storage for photos. reportlab PDFs (logo header, grey checklist). Emergent Resend email.
- Frontend: React 19 + React Router + Tailwind + shadcn/ui + Phosphor + recharts. Mobile-first + desktop sidebar.
- Master checklist: checklist_data.py (54 items / 6 sections, 1M/3M/12M, photo_points).
- Buildings master: data_buildings.json (1157 buildings) auto-loaded to `buildings`.

## Roles
admin, technician, supervisor, head_maintenance, sales, inventory, customer. Seeded on startup (see /app/memory/test_credentials.md). Owner Google admin: agus.supriyadi@gmail.com.

## Report Types
- SIR (Service Inspection Report) — routine 1M/3M/12M. Collection: `inspections`.
- ECR (Call Back / Work Report) — customer call-back outside routine. Collection: `reports` (report_type=ECR).
- HOR (Hand Over Report) — spare-part installation with before/after photos. Collection: `reports` (report_type=HOR).

## Implemented
- 2026-07-28: JWT auth, dynamic SIR checklist, 4-step wizard (measurements+photos, signatures), history, status workflow, spare-part follow-up dashboard, dashboard stats, SIR PDF, admin users. Testing 100%.
- 2026-08-10 (iter 2): Google login, building autofill, draft edit, 100% submit gating, spare-part change email notifications, PDF photo attachment page. Testing 100%.
- 2026-08-10 (iter 3): Standardized PDF filenames SIR/ECR/HOR-YYYYMMDD-JOB-SITE#UNIT; Fujitec logo at left of PDF header (title stays centered); grey checklist headers; supervisor/head can add signatures (checked_by/approved_by) & change status to checked/draft; approved-downgrade restricted to head_maintenance; ECR & HOR report types with full CRUD/status/signature/PDF; report chooser + list + detail; shared ReportWorkflow component. Testing 100% (55/55 backend + frontend flows).

## Known Minor (documented, out of scope)
- PDF download endpoints are public by UUID (used for <img>/inline view).
- Login rate-limit keyed on LB IP.

## Backlog / Next
- P1: Secure PDF endpoints with short-lived tokens.
- P2: Scope customer role to their own site(s); Excel export of history.
- P2: Daily digest email of pending spare parts; notifications on status change to owning teams.
- P2: ECR server-side submit validation (required fields); Pydantic model for reports.
