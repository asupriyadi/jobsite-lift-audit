"""Iteration 2 backend tests: buildings, gating, edit, PDF w/photo, google-session, spare notify."""
import io
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

CREDS = {
    "admin": ("admin@fujitec.com", "admin123"),
    "technician": ("teknisi@fujitec.com", "teknisi123"),
    "supervisor": ("supervisor@fujitec.com", "super123"),
    "head_maintenance": ("kepala@fujitec.com", "kepala123"),
    "sales": ("sales@fujitec.com", "sales123"),
    "inventory": ("inventory@fujitec.com", "inv123"),
    "customer": ("customer@fujitec.com", "cust123"),
}
_tokens = {}


def _login(role):
    if role in _tokens:
        return _tokens[role]
    email, pw = CREDS[role]
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=30)
    assert r.status_code == 200, r.text
    _tokens[role] = r.json()["access_token"]
    return _tokens[role]


def _h(role):
    return {"Authorization": f"Bearer {_login(role)}"}


# ---------- Buildings (Master Gedung) ----------
def test_building_lookup_exact():
    r = requests.get(f"{API}/buildings/lookup?job_number=ZEZ3624", headers=_h("technician"), timeout=30)
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc, f"expected a building for ZEZ3624, got {doc}"
    assert doc.get("site_name") == "ST REGIST #LH1", doc


def test_building_lookup_missing_returns_empty():
    r = requests.get(f"{API}/buildings/lookup?job_number=___NOT_A_JOB___", headers=_h("technician"), timeout=30)
    assert r.status_code == 200
    assert r.json() == {}


def test_building_search():
    r = requests.get(f"{API}/buildings?q=ST%20REGIST", headers=_h("technician"), timeout=30)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    assert len(rows) >= 1
    assert all("job_number" in row and "site_name" in row for row in rows)


# ---------- 100% checklist gating ----------
def _min_checklist_payload(status="draft", all_judged=False):
    items = [
        {"no": 1, "section": "S", "description": "d1", "photo_points": 0,
         "judgment": "good" if all_judged else None, "remark": "", "points": []},
        {"no": 2, "section": "S", "description": "d2", "photo_points": 0,
         "judgment": "good" if all_judged else None, "remark": "", "points": []},
    ]
    return {
        "job_number": "TEST-GATE-001",
        "site_name": "TEST_Gating",
        "inspection_date": "2026-01-16",
        "time_from": "08:00", "time_to": "10:00",
        "serviced_by": "Budi", "total_units": 1, "lift_number": "L1",
        "checklist_type": "1M", "items": items,
        "global_remark": "", "spare_parts": [],
        "signatures": {}, "status": status,
    }


def test_submit_incomplete_returns_400():
    payload = _min_checklist_payload(status="submitted", all_judged=False)
    r = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload, timeout=30)
    assert r.status_code == 400, r.text
    detail = r.json().get("detail", "")
    # Indonesian message expected
    assert "belum" in detail.lower() or "draft" in detail.lower(), detail


def test_draft_incomplete_saves_ok():
    payload = _min_checklist_payload(status="draft", all_judged=False)
    r = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload, timeout=30)
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["status"] == "draft"
    # cleanup
    requests.delete(f"{API}/inspections/{doc['id']}", headers=_h("admin"), timeout=30)


def test_submit_complete_1m_all_items_ok():
    # Load 1M checklist master and fully judge every item
    m = requests.get(f"{API}/checklist/master?type=1M", headers=_h("technician"), timeout=30).json()
    items = []
    for it in m["items"]:
        items.append({
            "no": it["no"], "section": it["section"], "description": it["description"],
            "photo_points": it.get("photo_points", 0),
            "judgment": "good", "remark": "", "points": []
        })
    payload = {
        "job_number": "TEST-GATE-FULL", "site_name": "TEST_Full",
        "inspection_date": "2026-01-16", "time_from": "08:00", "time_to": "10:00",
        "serviced_by": "Budi", "total_units": 1, "lift_number": "L1",
        "checklist_type": "1M", "items": items,
        "global_remark": "", "spare_parts": [],
        "signatures": {}, "status": "submitted",
    }
    r = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload, timeout=30)
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["status"] == "submitted"
    requests.delete(f"{API}/inspections/{doc['id']}", headers=_h("admin"), timeout=30)


# ---------- Edit rules ----------
_edit_ctx = {}


def test_create_draft_for_edit():
    payload = _min_checklist_payload(status="draft", all_judged=False)
    payload["job_number"] = "TEST-EDIT-001"
    r = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload, timeout=30)
    assert r.status_code == 200
    _edit_ctx["id"] = r.json()["id"]


def test_technician_can_edit_own_draft():
    payload = _min_checklist_payload(status="draft", all_judged=False)
    payload["job_number"] = "TEST-EDIT-001"
    payload["site_name"] = "TEST_EditedSite"
    r = requests.put(f"{API}/inspections/{_edit_ctx['id']}", headers=_h("technician"),
                     json=payload, timeout=30)
    assert r.status_code == 200, r.text
    assert r.json()["site_name"] == "TEST_EditedSite"


def test_edit_forbidden_after_submit():
    # Submit the draft (via PUT with full judgment)
    m = requests.get(f"{API}/checklist/master?type=1M", headers=_h("technician")).json()
    items = [{"no": it["no"], "section": it["section"], "description": it["description"],
              "photo_points": it.get("photo_points", 0), "judgment": "good",
              "remark": "", "points": []} for it in m["items"]]
    payload = {
        "job_number": "TEST-EDIT-001", "site_name": "TEST_EditedSite",
        "inspection_date": "2026-01-16", "time_from": "08:00", "time_to": "10:00",
        "serviced_by": "Budi", "total_units": 1, "lift_number": "L1",
        "checklist_type": "1M", "items": items,
        "global_remark": "", "spare_parts": [], "signatures": {}, "status": "submitted",
    }
    r = requests.put(f"{API}/inspections/{_edit_ctx['id']}", headers=_h("technician"),
                     json=payload, timeout=30)
    assert r.status_code == 200, r.text
    # Now technician can no longer edit
    r2 = requests.put(f"{API}/inspections/{_edit_ctx['id']}", headers=_h("technician"),
                      json=payload, timeout=30)
    assert r2.status_code == 403, r2.text
    detail = r2.json().get("detail", "")
    assert "tidak dapat diedit" in detail.lower() or "dikirim" in detail.lower(), detail
    # cleanup
    requests.delete(f"{API}/inspections/{_edit_ctx['id']}", headers=_h("admin"), timeout=30)


# ---------- PDF with photo attachment ----------
def test_pdf_with_photo_attachment_larger():
    # 1) Upload a real PNG (a bit bigger to be sure)
    png = bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000200000002008060000007377A8"
        "F60000004049444154789CEDCDB10D00200803404BF6DF75760610A6C10122A5"
        "44FF7D2FEF00000000000000000000000000000000000000000000000000000000"
        "0000000000000000000000004E1C0F110001B7A96A8B0000000049454E44AE426082"
    )
    files = {"file": ("t.png", io.BytesIO(png), "image/png")}
    up = requests.post(f"{API}/upload", headers=_h("technician"), files=files, timeout=60)
    assert up.status_code == 200, up.text
    file_id = up.json()["file_id"]

    # 2) Create a 1M inspection with item 45 having a photo
    m = requests.get(f"{API}/checklist/master?type=1M", headers=_h("technician")).json()
    items = []
    for it in m["items"]:
        entry = {"no": it["no"], "section": it["section"], "description": it["description"],
                 "photo_points": it.get("photo_points", 0), "judgment": "good",
                 "remark": "", "points": []}
        if it["no"] == 45 and it.get("photo_points", 0) >= 1:
            entry["points"] = [{"index": 0, "measurement": "1.0mm", "photo_file_id": file_id}]
        items.append(entry)
    payload_with = {
        "job_number": "TEST-PDF-PHOTO", "site_name": "TEST_PDFPhoto",
        "inspection_date": "2026-01-16", "time_from": "08:00", "time_to": "10:00",
        "serviced_by": "Budi", "total_units": 1, "lift_number": "L1",
        "checklist_type": "1M", "items": items, "global_remark": "",
        "spare_parts": [], "signatures": {}, "status": "submitted",
    }
    r_with = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload_with, timeout=30)
    assert r_with.status_code == 200, r_with.text
    id_with = r_with.json()["id"]

    # 3) Same but with no photo
    items2 = []
    for it in m["items"]:
        items2.append({"no": it["no"], "section": it["section"], "description": it["description"],
                       "photo_points": it.get("photo_points", 0), "judgment": "good",
                       "remark": "", "points": []})
    payload_no = dict(payload_with, items=items2, job_number="TEST-PDF-NOPHOTO")
    r_no = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload_no, timeout=30)
    assert r_no.status_code == 200, r_no.text
    id_no = r_no.json()["id"]

    # 4) Compare PDF sizes
    pdf_with = requests.get(f"{API}/inspections/{id_with}/pdf", timeout=60)
    pdf_no = requests.get(f"{API}/inspections/{id_no}/pdf", timeout=60)
    assert pdf_with.status_code == 200 and pdf_no.status_code == 200
    assert pdf_with.headers["content-type"].startswith("application/pdf")
    assert pdf_with.content[:4] == b"%PDF"
    # The photo attachment page should make it larger
    assert len(pdf_with.content) > len(pdf_no.content), (
        f"expected photo PDF larger, got {len(pdf_with.content)} vs {len(pdf_no.content)}"
    )

    # cleanup
    for i in (id_with, id_no):
        requests.delete(f"{API}/inspections/{i}", headers=_h("admin"), timeout=30)


# ---------- Google session ----------
def test_google_session_invalid_returns_401():
    r = requests.post(f"{API}/auth/google-session", json={"session_id": "invalid-xxxx"}, timeout=30)
    assert r.status_code == 401, r.text


# ---------- Spare part change (email best-effort) ----------
def test_spare_part_change_inventory_ok():
    # Create an inspection with a spare part as technician
    m = requests.get(f"{API}/checklist/master?type=1M", headers=_h("technician")).json()
    items = [{"no": it["no"], "section": it["section"], "description": it["description"],
              "photo_points": it.get("photo_points", 0), "judgment": "good",
              "remark": "", "points": []} for it in m["items"]]
    payload = {
        "job_number": "TEST-SPARE-EMAIL", "site_name": "TEST_SpareEmail",
        "inspection_date": "2026-01-16", "time_from": "08:00", "time_to": "10:00",
        "serviced_by": "Budi", "total_units": 1, "lift_number": "L1",
        "checklist_type": "1M", "items": items, "global_remark": "",
        "spare_parts": [{"name": "TEST_Roller", "quantity": "1"}],
        "signatures": {}, "status": "submitted",
    }
    r = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload, timeout=30)
    assert r.status_code == 200
    doc = r.json()
    insp_id, spare_id = doc["id"], doc["spare_parts"][0]["id"]

    # inventory role updates inventory_status -> should be 200 even if email fails
    up = requests.patch(f"{API}/inspections/{insp_id}/spare-parts/{spare_id}",
                        headers=_h("inventory"),
                        json={"field": "inventory_status", "value": "available"},
                        timeout=60)
    assert up.status_code == 200, up.text
    # sales trying to change inventory_status -> 403
    denied = requests.patch(f"{API}/inspections/{insp_id}/spare-parts/{spare_id}",
                            headers=_h("sales"),
                            json={"field": "inventory_status", "value": "available"},
                            timeout=30)
    assert denied.status_code == 403

    requests.delete(f"{API}/inspections/{insp_id}", headers=_h("admin"), timeout=30)
