"""End-to-end backend test suite for Fujitec SIR app."""
import io
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # fallback to loading from /app/frontend/.env
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
    assert r.status_code == 200, f"login {role} failed: {r.status_code} {r.text}"
    body = r.json()
    assert body["user"]["role"] == role
    _tokens[role] = body["access_token"]
    return _tokens[role]


def _h(role):
    return {"Authorization": f"Bearer {_login(role)}"}


# -------- Auth --------
@pytest.mark.parametrize("role", list(CREDS.keys()))
def test_login_each_role(role):
    email, pw = CREDS[role]
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == email
    assert data["user"]["role"] == role


def test_login_invalid():
    r = requests.post(f"{API}/auth/login", json={"email": "admin@fujitec.com", "password": "wrong"}, timeout=30)
    assert r.status_code == 401


def test_auth_me():
    r = requests.get(f"{API}/auth/me", headers=_h("technician"), timeout=30)
    assert r.status_code == 200
    assert r.json()["role"] == "technician"


# -------- Checklist master --------
def test_checklist_counts_and_photo_points():
    counts = {}
    photo_map = {}
    for t in ["1M", "3M", "12M"]:
        r = requests.get(f"{API}/checklist/master?type={t}", headers=_h("technician"), timeout=30)
        assert r.status_code == 200, r.text
        items = r.json()["items"]
        counts[t] = len(items)
        photo_map[t] = {i["no"]: i["photo_points"] for i in items}
    # differ
    assert counts["1M"] != counts["3M"] != counts["12M"], counts
    # 12M should include items 10, 45, 47 with photo_points > 0
    assert photo_map["12M"].get(10, 0) == 5
    assert photo_map["12M"].get(45, 0) == 1
    assert photo_map["12M"].get(47, 0) == 2


def test_checklist_invalid_type():
    r = requests.get(f"{API}/checklist/master?type=BAD", headers=_h("technician"), timeout=30)
    assert r.status_code == 400


# -------- Inspection lifecycle --------
_created_inspection = {}


def test_create_full_inspection():
    payload = {
        "job_number": "TEST-JOB-001",
        "site_name": "TEST_Site A",
        "inspection_date": "2026-01-15",
        "time_from": "08:00",
        "time_to": "10:00",
        "serviced_by": "Budi Teknisi",
        "total_units": 2,
        "lift_number": "L1",
        "checklist_type": "12M",
        "items": [
            {"no": 1, "section": "ELEVATOR OPERATION", "description": "Running", "photo_points": 0, "judgment": "good", "remark": "ok", "points": []},
            {"no": 10, "section": "MOTOR ROOM", "description": "Main Sheave", "photo_points": 5, "judgment": "replaced", "remark": "worn",
             "points": [{"index": i, "measurement": f"{i}.5mm"} for i in range(5)]},
            {"no": 47, "section": "PIT", "description": "Overload", "photo_points": 2, "judgment": "damage", "remark": "cracked", "points": [{"index": 0, "measurement": "2mm"}, {"index": 1, "measurement": "3mm"}]},
        ],
        "global_remark": "TEST global remark",
        "spare_parts": [
            {"name": "TEST_BrakePad", "quantity": "2 pcs"},
            {"name": "TEST_Roller", "quantity": "4"},
        ],
        "signatures": {
            "issued_by": {"name": "Budi", "image": "data:image/png;base64,xx"},
            "customer": {"name": "Cust", "image": "data:image/png;base64,xx"},
            "checked_by": {"name": "", "image": ""},
            "approved_by": {"name": "", "image": ""},
        },
        "status": "submitted",
    }
    r = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload, timeout=30)
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["job_number"] == "TEST-JOB-001"
    assert doc["status"] == "submitted"
    assert len(doc["spare_parts"]) == 2
    assert doc["spare_parts"][0]["sales_status"] == "pending"
    _created_inspection["id"] = doc["id"]
    _created_inspection["spare_id"] = doc["spare_parts"][0]["id"]
    _created_inspection["spare_id2"] = doc["spare_parts"][1]["id"]


def test_list_inspections_includes_created():
    r = requests.get(f"{API}/inspections", headers=_h("technician"), timeout=30)
    assert r.status_code == 200
    ids = [d["id"] for d in r.json()]
    assert _created_inspection["id"] in ids


def test_get_inspection_by_id():
    r = requests.get(f"{API}/inspections/{_created_inspection['id']}", headers=_h("supervisor"), timeout=30)
    assert r.status_code == 200
    assert r.json()["global_remark"] == "TEST global remark"


# -------- Status workflow --------
def test_technician_cannot_check():
    r = requests.patch(f"{API}/inspections/{_created_inspection['id']}/status",
                       headers=_h("technician"), json={"status": "checked"}, timeout=30)
    assert r.status_code == 403


def test_supervisor_can_check():
    r = requests.patch(f"{API}/inspections/{_created_inspection['id']}/status",
                       headers=_h("supervisor"), json={"status": "checked"}, timeout=30)
    assert r.status_code == 200
    assert r.json()["status"] == "checked"


def test_supervisor_cannot_approve():
    r = requests.patch(f"{API}/inspections/{_created_inspection['id']}/status",
                       headers=_h("supervisor"), json={"status": "approved"}, timeout=30)
    assert r.status_code == 403


def test_head_maintenance_can_approve():
    r = requests.patch(f"{API}/inspections/{_created_inspection['id']}/status",
                       headers=_h("head_maintenance"), json={"status": "approved"}, timeout=30)
    assert r.status_code == 200


# -------- Spare part authorization --------
def test_sales_can_update_sales_status():
    r = requests.patch(f"{API}/inspections/{_created_inspection['id']}/spare-parts/{_created_inspection['spare_id']}",
                       headers=_h("sales"), json={"field": "sales_status", "value": "offered"}, timeout=30)
    assert r.status_code == 200


def test_sales_cannot_update_inventory_status():
    r = requests.patch(f"{API}/inspections/{_created_inspection['id']}/spare-parts/{_created_inspection['spare_id']}",
                       headers=_h("sales"), json={"field": "inventory_status", "value": "available"}, timeout=30)
    assert r.status_code == 403


def test_inventory_can_update_inventory_status():
    r = requests.patch(f"{API}/inspections/{_created_inspection['id']}/spare-parts/{_created_inspection['spare_id']}",
                       headers=_h("inventory"), json={"field": "inventory_status", "value": "available"}, timeout=30)
    assert r.status_code == 200


def test_customer_can_update_po():
    r = requests.patch(f"{API}/inspections/{_created_inspection['id']}/spare-parts/{_created_inspection['spare_id']}",
                       headers=_h("customer"), json={"field": "customer_po_status", "value": "po_issued"}, timeout=30)
    assert r.status_code == 200


def test_customer_cannot_update_sales_status():
    r = requests.patch(f"{API}/inspections/{_created_inspection['id']}/spare-parts/{_created_inspection['spare_id']}",
                       headers=_h("customer"), json={"field": "sales_status", "value": "offered"}, timeout=30)
    assert r.status_code == 403


def test_spare_parts_aggregation():
    r = requests.get(f"{API}/spare-parts", headers=_h("sales"), timeout=30)
    assert r.status_code == 200
    rows = r.json()
    assert any(x.get("inspection_id") == _created_inspection["id"] for x in rows)
    # aggregation includes inspection metadata
    row = next(x for x in rows if x.get("inspection_id") == _created_inspection["id"])
    assert row["job_number"] == "TEST-JOB-001"
    assert "site_name" in row


def test_spare_parts_filters():
    r = requests.get(f"{API}/spare-parts?inventory_status=available", headers=_h("inventory"), timeout=30)
    assert r.status_code == 200
    for x in r.json():
        assert x["inventory_status"] == "available"

    r2 = requests.get(f"{API}/spare-parts?only_open=true", headers=_h("inventory"), timeout=30)
    assert r2.status_code == 200


# -------- Dashboard stats --------
def test_dashboard_stats():
    r = requests.get(f"{API}/dashboard/stats", headers=_h("admin"), timeout=30)
    assert r.status_code == 200
    s = r.json()
    for k in ["total_inspections", "by_status", "by_type", "spare_total", "spare_open", "inventory_breakdown", "recent"]:
        assert k in s
    assert s["total_inspections"] >= 1
    assert isinstance(s["recent"], list)


# -------- Upload --------
_uploaded = {}


def test_upload_and_download_image():
    # 1x1 png bytes
    png = bytes.fromhex("89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4890000000A49444154789C6300010000000500010D0A2DB40000000049454E44AE426082")
    files = {"file": ("test.png", io.BytesIO(png), "image/png")}
    r = requests.post(f"{API}/upload", headers=_h("technician"), files=files, timeout=60)
    assert r.status_code == 200, r.text
    fid = r.json()["file_id"]
    _uploaded["id"] = fid
    r2 = requests.get(f"{API}/files/{fid}", timeout=60)
    assert r2.status_code == 200
    assert r2.headers.get("content-type", "").startswith("image/")


# -------- PDF export --------
def test_pdf_export():
    _tk = requests.get(f"{API}/inspections/{_created_inspection['id']}/pdf-token", headers=_h("admin"), timeout=30).json()["token"]
    r = requests.get(f"{API}/inspections/{_created_inspection['id']}/pdf?auth={_tk}", timeout=60)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content[:4] == b"%PDF"


# -------- Admin users --------
def test_admin_create_and_list_user():
    import time
    email = f"test_user_{int(time.time())}@example.com"
    r = requests.post(f"{API}/users", headers=_h("admin"),
                      json={"email": email, "password": "pass1234", "name": "TEST_User", "role": "technician"},
                      timeout=30)
    assert r.status_code == 200, r.text
    r2 = requests.get(f"{API}/users", headers=_h("admin"), timeout=30)
    assert r2.status_code == 200
    assert any(u["email"] == email for u in r2.json())
    # cleanup
    uid = next(u["id"] for u in r2.json() if u["email"] == email)
    requests.delete(f"{API}/users/{uid}", headers=_h("admin"), timeout=30)


def test_non_admin_cannot_create_user():
    r = requests.post(f"{API}/users", headers=_h("technician"),
                      json={"email": "x@y.z", "password": "pass1234", "name": "x", "role": "technician"},
                      timeout=30)
    assert r.status_code == 403
