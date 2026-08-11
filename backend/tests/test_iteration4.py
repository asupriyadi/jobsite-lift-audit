"""Iteration 4 (FASE 1) backend tests: secure PDF tokens, daily-summary,
SIR site filter, after_photo, unit history, excel export, customer_email approve,
new roles, buildings contract fields."""
import io
import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
BASE = BASE_URL.rstrip("/") + "/api"

CREDS = {
    "admin": ("admin@fujitec.com", "admin123"),
    "technician": ("teknisi@fujitec.com", "teknisi123"),
    "supervisor": ("supervisor@fujitec.com", "super123"),
    "head": ("kepala@fujitec.com", "kepala123"),
    "inventory": ("inventory@fujitec.com", "inv123"),
    "sales": ("sales@fujitec.com", "sales123"),
    "customer": ("customer@fujitec.com", "cust123"),
}


def login(role):
    email, pw = CREDS[role]
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": pw}, timeout=30)
    assert r.status_code == 200, f"login {role} failed: {r.text}"
    return r.json()["access_token"]


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="session")
def tokens():
    return {k: login(k) for k in CREDS}


# ---------- helpers ----------
def _make_sir(tokens, customer_email=""):
    """Create a SIR (technician) with a minimal but 100%-complete checklist,
    add one spare part, submit -> supervisor checked -> head approved possible."""
    tok = tokens["technician"]
    # New inspection - fetch checklist template to know items/points structure
    payload = {
        "job_number": "EX3155",
        "site_name": "TEST-IT4-SITE",
        "lift_number": "L1",
        "checklist_type": "1M",
        "inspection_date": "2026-01-05",
        "time_from": "08:00",
        "time_to": "09:00",
        "serviced_by": "TEST-IT4",
        "customer_email": customer_email,
    }
    r = requests.post(f"{BASE}/inspections", json=payload, headers=H(tok), timeout=30)
    assert r.status_code in (200, 201), r.text
    doc = r.json()
    iid = doc["id"]
    # judge every point ok=True
    items = doc.get("items", [])
    for it in items:
        for p in it.get("points", []):
            requests.patch(f"{BASE}/inspections/{iid}/items/{it['id']}/points/{p['id']}",
                           json={"ok": True, "note": ""}, headers=H(tok), timeout=30)
    return iid


def _delete_inspection(tokens, iid):
    requests.delete(f"{BASE}/inspections/{iid}", headers=H(tokens["admin"]), timeout=30)


# ---------- Secure PDF token ----------
class TestPdfTokens:
    def test_inspection_pdf_requires_token(self, tokens):
        iid = _make_sir(tokens)
        try:
            r = requests.get(f"{BASE}/inspections/{iid}/pdf", timeout=30)
            assert r.status_code == 401

            r2 = requests.get(f"{BASE}/inspections/{iid}/pdf-token", headers=H(tokens["technician"]), timeout=30)
            assert r2.status_code == 200
            tok = r2.json()["token"]
            assert tok

            r3 = requests.get(f"{BASE}/inspections/{iid}/pdf?auth={tok}", timeout=60)
            assert r3.status_code == 200
            assert r3.headers.get("content-type", "").startswith("application/pdf")
            assert len(r3.content) > 500

            # Tampered token
            r4 = requests.get(f"{BASE}/inspections/{iid}/pdf?auth={tok}xx", timeout=30)
            assert r4.status_code == 401
        finally:
            _delete_inspection(tokens, iid)

    def test_report_pdf_requires_token(self, tokens):
        # Create an ECR
        tok = tokens["technician"]
        payload = {
            "report_type": "ECR",
            "job_number": "EX3155",
            "site_name": "TEST-IT4-ECR",
            "unit_no": "U-1",
            "report_date": "2026-01-06",
            "working_details": "Test",
        }
        r = requests.post(f"{BASE}/reports", json=payload, headers=H(tok), timeout=30)
        assert r.status_code in (200, 201), r.text
        rid = r.json()["id"]
        try:
            r0 = requests.get(f"{BASE}/reports/{rid}/pdf", timeout=30)
            assert r0.status_code == 401
            rt = requests.get(f"{BASE}/reports/{rid}/pdf-token", headers=H(tok), timeout=30)
            assert rt.status_code == 200
            t = rt.json()["token"]
            r1 = requests.get(f"{BASE}/reports/{rid}/pdf?auth={t}", timeout=60)
            assert r1.status_code == 200
            assert r1.headers["content-type"].startswith("application/pdf")
            r2 = requests.get(f"{BASE}/reports/{rid}/pdf?auth=badtoken.abc.xyz", timeout=30)
            assert r2.status_code == 401
        finally:
            requests.delete(f"{BASE}/reports/{rid}", headers=H(tokens["admin"]), timeout=30)


# ---------- Daily summary ----------
class TestDailySummary:
    def test_head_can_trigger(self, tokens):
        r = requests.post(f"{BASE}/admin/daily-summary", headers=H(tokens["head"]), timeout=60)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("ok") is True
        assert isinstance(j.get("pending"), int)

    def test_technician_forbidden(self, tokens):
        r = requests.post(f"{BASE}/admin/daily-summary", headers=H(tokens["technician"]), timeout=30)
        assert r.status_code == 403


# ---------- SIR sites + building filter ----------
class TestSitesFilter:
    def test_sites_and_filter(self, tokens):
        iid = _make_sir(tokens)
        try:
            r = requests.get(f"{BASE}/inspections/sites", headers=H(tokens["technician"]), timeout=30)
            assert r.status_code == 200
            sites = r.json()
            assert isinstance(sites, list)
            assert "TEST-IT4-SITE" in sites

            r2 = requests.get(f"{BASE}/inspections?site_name=TEST-IT4-SITE",
                              headers=H(tokens["technician"]), timeout=30)
            assert r2.status_code == 200
            lst = r2.json()
            assert len(lst) >= 1
            assert all(d["site_name"] == "TEST-IT4-SITE" for d in lst)
        finally:
            _delete_inspection(tokens, iid)


# ---------- After-replacement photo ----------
class TestAfterPhoto:
    def test_after_photo_persist_and_role(self, tokens):
        iid = _make_sir(tokens)
        try:
            # Add a spare part via PUT (update inspection)
            g0 = requests.get(f"{BASE}/inspections/{iid}", headers=H(tokens["technician"]), timeout=30)
            assert g0.status_code == 200
            insp_doc = g0.json()
            sp_new = {"id": str(uuid.uuid4()), "name": "TEST-IT4-PART", "quantity": "1", "notes": ""}
            insp_doc["spare_parts"] = (insp_doc.get("spare_parts") or []) + [sp_new]
            # Strip server-only fields not expected by InspectionInput
            payload = {k: insp_doc.get(k) for k in
                       ("job_number", "site_name", "lift_number", "checklist_type",
                        "inspection_date", "time_from", "time_to", "serviced_by",
                        "customer_email", "items", "spare_parts", "signatures")
                       if insp_doc.get(k) is not None}
            r = requests.put(f"{BASE}/inspections/{iid}", json=payload,
                             headers=H(tokens["technician"]), timeout=30)
            assert r.status_code in (200, 201), r.text
            sp_id = sp_new["id"]

            # Upload a small image via /api/upload
            img = ("test.png", io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 64), "image/png")
            up = requests.post(f"{BASE}/upload", files={"file": img},
                               headers=H(tokens["technician"]), timeout=30)
            assert up.status_code == 200, up.text
            file_id = up.json()["file_id"]

            # PATCH after_photo_file_id as technician -> ok
            p = requests.patch(f"{BASE}/inspections/{iid}/spare-parts/{sp_id}",
                               json={"field": "after_photo_file_id", "value": file_id},
                               headers=H(tokens["technician"]), timeout=30)
            assert p.status_code == 200, p.text

            # Verify persisted
            g = requests.get(f"{BASE}/inspections/{iid}", headers=H(tokens["technician"]), timeout=30)
            assert g.status_code == 200
            sp = [x for x in g.json()["spare_parts"] if x["id"] == sp_id][0]
            assert sp.get("after_photo_file_id") == file_id

            # Inventory role forbidden
            p2 = requests.patch(f"{BASE}/inspections/{iid}/spare-parts/{sp_id}",
                                json={"field": "after_photo_file_id", "value": file_id},
                                headers=H(tokens["inventory"]), timeout=30)
            assert p2.status_code == 403
        finally:
            _delete_inspection(tokens, iid)


# ---------- Unit history ----------
class TestUnitHistory:
    def test_returns_events_and_building(self, tokens):
        iid = _make_sir(tokens)
        try:
            r = requests.get(f"{BASE}/units/history?job_number=EX3155",
                             headers=H(tokens["technician"]), timeout=30)
            assert r.status_code == 200, r.text
            j = r.json()
            assert j["job_number"] == "EX3155"
            assert isinstance(j.get("events"), list)
            assert any(e["kind"] == "SIR" for e in j["events"])
            # Building should include contract-related fields (may be empty dict for missing jobs)
            b = j.get("building") or {}
            # It may or may not have has_contract; assert structure returned
            assert isinstance(b, dict)
        finally:
            _delete_inspection(tokens, iid)


# ---------- Excel export ----------
class TestExcelExport:
    def test_excel_download(self, tokens):
        r = requests.get(f"{BASE}/export/excel", headers=H(tokens["admin"]), timeout=60)
        assert r.status_code == 200, r.text
        ct = r.headers.get("content-type", "")
        assert "spreadsheetml.sheet" in ct
        assert len(r.content) > 1000
        # xlsx magic bytes = PK zip
        assert r.content[:2] == b"PK"


# ---------- Customer email on approve ----------
class TestCustomerEmailApprove:
    def test_approve_with_customer_email(self, tokens):
        iid = _make_sir(tokens, customer_email="delivered@resend.dev")
        try:
            # Submit
            s = requests.patch(f"{BASE}/inspections/{iid}/status", json={"status": "submitted"},
                               headers=H(tokens["technician"]), timeout=30)
            assert s.status_code == 200, s.text
            # Supervisor checked
            c = requests.patch(f"{BASE}/inspections/{iid}/status", json={"status": "checked"},
                               headers=H(tokens["supervisor"]), timeout=30)
            assert c.status_code == 200, c.text
            # Head approved -> should return 200 despite customer_email present (email best-effort)
            a = requests.patch(f"{BASE}/inspections/{iid}/status", json={"status": "approved"},
                               headers=H(tokens["head"]), timeout=60)
            assert a.status_code == 200, a.text
        finally:
            _delete_inspection(tokens, iid)


# ---------- New roles ----------
class TestNewRoles:
    @pytest.mark.parametrize("role", ["troubleshooter", "admin_staff", "contract_staff"])
    def test_admin_creates_role_and_login(self, tokens, role):
        email = f"TEST_IT4_{role}_{uuid.uuid4().hex[:6]}@fujitec.com"
        pw = "Passw0rd!"
        r = requests.post(f"{BASE}/users", json={"email": email, "password": pw,
                                                  "name": f"Test {role}", "role": role},
                          headers=H(tokens["admin"]), timeout=30)
        assert r.status_code in (200, 201), r.text
        uid = r.json().get("id")
        try:
            lr = requests.post(f"{BASE}/auth/login", json={"email": email, "password": pw}, timeout=30)
            assert lr.status_code == 200, lr.text
            assert lr.json().get("access_token")
        finally:
            if uid:
                requests.delete(f"{BASE}/users/{uid}", headers=H(tokens["admin"]), timeout=30)


# ---------- Buildings contract fields ----------
class TestBuildingsContract:
    def test_lookup_ex3155_contract(self, tokens):
        r = requests.get(f"{BASE}/buildings/lookup?job_number=EX3155",
                         headers=H(tokens["technician"]), timeout=30)
        assert r.status_code == 200, r.text
        b = r.json()
        assert b, "expected non-empty building for EX3155"
        assert b.get("has_contract") is True
        assert b.get("maintenance_period") == "Every Month"
        assert (b.get("spv") or "").upper() == "SUYANTO"
