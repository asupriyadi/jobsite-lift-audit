"""Iteration 3 backend tests: SIR PDF filename+logo, SIR status workflow (with approved-downgrade rules),
SIR add-signature, ECR & HOR CRUD/status/signature/delete + PDF filenames, invalid report_type."""
import io
import os
import re
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


def _full_1m_payload(status="submitted", job="TEST-IT3-001", site="TEST_Site_IT3", lift="L1", date="2026-01-16"):
    m = requests.get(f"{API}/checklist/master?type=1M", headers=_h("technician")).json()
    items = [{"no": it["no"], "section": it["section"], "description": it["description"],
              "photo_points": it.get("photo_points", 0), "judgment": "good",
              "remark": "", "points": []} for it in m["items"]]
    return {
        "job_number": job, "site_name": site,
        "inspection_date": date, "time_from": "08:00", "time_to": "10:00",
        "serviced_by": "Budi", "total_units": 1, "lift_number": lift,
        "checklist_type": "1M", "items": items,
        "global_remark": "", "spare_parts": [],
        "signatures": {}, "status": status,
    }


# =========================================================================
# (A) SIR PDF filename + application/pdf
# =========================================================================
def test_sir_pdf_filename_and_type():
    payload = _full_1m_payload(status="submitted", job="EX3155", site="TEST_PDFNAME", lift="U1",
                               date="2026-02-03")
    r = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload, timeout=30)
    assert r.status_code == 200, r.text
    insp_id = r.json()["id"]
    try:
        _t = requests.get(f"{API}/inspections/{insp_id}/pdf-token", headers=_h("technician"), timeout=30).json()["token"]
        p = requests.get(f"{API}/inspections/{insp_id}/pdf?auth={_t}", timeout=60)
        assert p.status_code == 200
        assert p.headers["content-type"].startswith("application/pdf")
        assert p.content[:4] == b"%PDF"
        cd = p.headers.get("content-disposition", "")
        # Should look like: filename="SIR-20260203-EX3155-TEST_PDFNAME#U1.pdf"
        m = re.search(r'filename="?([^";]+)"?', cd)
        assert m, f"missing filename in Content-Disposition: {cd}"
        fname = m.group(1)
        assert fname.startswith("SIR-"), fname
        # 8-digit date directly after SIR-
        assert re.match(r"SIR-\d{8}-", fname), fname
        assert "EX3155" in fname
        assert "TEST_PDFNAME" in fname
        assert fname.endswith(".pdf")
    finally:
        requests.delete(f"{API}/inspections/{insp_id}", headers=_h("admin"), timeout=30)


# =========================================================================
# (B) SIR status workflow & downgrade rules
# =========================================================================
def test_sir_status_workflow_and_downgrade_rules():
    payload = _full_1m_payload(status="submitted", job="TEST-IT3-FLOW", site="TEST_Flow", lift="LF1")
    r = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload, timeout=30)
    assert r.status_code == 200
    iid = r.json()["id"]
    try:
        # technician cannot mark checked
        r1 = requests.patch(f"{API}/inspections/{iid}/status", headers=_h("technician"),
                            json={"status": "checked"}, timeout=30)
        assert r1.status_code == 403, r1.text

        # supervisor -> checked
        r2 = requests.patch(f"{API}/inspections/{iid}/status", headers=_h("supervisor"),
                            json={"status": "checked"}, timeout=30)
        assert r2.status_code == 200, r2.text
        assert r2.json()["status"] == "checked"

        # supervisor -> draft (from checked, still not approved yet)
        r3 = requests.patch(f"{API}/inspections/{iid}/status", headers=_h("supervisor"),
                            json={"status": "draft"}, timeout=30)
        assert r3.status_code == 200, r3.text

        # push back to submitted -> checked -> approved by head
        requests.patch(f"{API}/inspections/{iid}/status", headers=_h("technician"),
                       json={"status": "submitted"}, timeout=30)
        requests.patch(f"{API}/inspections/{iid}/status", headers=_h("supervisor"),
                       json={"status": "checked"}, timeout=30)
        r4 = requests.patch(f"{API}/inspections/{iid}/status", headers=_h("head_maintenance"),
                            json={"status": "approved"}, timeout=30)
        assert r4.status_code == 200, r4.text

        # supervisor cannot downgrade from approved to checked or draft
        r5 = requests.patch(f"{API}/inspections/{iid}/status", headers=_h("supervisor"),
                            json={"status": "checked"}, timeout=30)
        assert r5.status_code == 403, r5.text
        r6 = requests.patch(f"{API}/inspections/{iid}/status", headers=_h("supervisor"),
                            json={"status": "draft"}, timeout=30)
        assert r6.status_code == 403, r6.text

        # head_maintenance CAN downgrade from approved
        r7 = requests.patch(f"{API}/inspections/{iid}/status", headers=_h("head_maintenance"),
                            json={"status": "checked"}, timeout=30)
        assert r7.status_code == 200, r7.text
        r8 = requests.patch(f"{API}/inspections/{iid}/status", headers=_h("head_maintenance"),
                            json={"status": "draft"}, timeout=30)
        # from checked (not approved) draft is allowed for head too
        assert r8.status_code == 200, r8.text
    finally:
        requests.delete(f"{API}/inspections/{iid}", headers=_h("admin"), timeout=30)


# =========================================================================
# (C) SIR add-signature
# =========================================================================
def test_sir_add_signature_role_gating():
    payload = _full_1m_payload(status="submitted", job="TEST-IT3-SIG", site="TEST_Sig", lift="LS1")
    r = requests.post(f"{API}/inspections", headers=_h("technician"), json=payload, timeout=30)
    iid = r.json()["id"]
    try:
        sig_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        # supervisor adds checked_by
        rc = requests.patch(f"{API}/inspections/{iid}/signature", headers=_h("supervisor"),
                            json={"key": "checked_by", "signature": {"name": "Sari S", "image": sig_img}}, timeout=30)
        assert rc.status_code == 200, rc.text
        # persists in GET
        got = requests.get(f"{API}/inspections/{iid}", headers=_h("supervisor"), timeout=30).json()
        assert got["signatures"]["checked_by"]["name"] == "Sari S"
        assert got["signatures"]["checked_by"]["image"].startswith("data:image/png")

        # technician cannot add approved_by
        rt = requests.patch(f"{API}/inspections/{iid}/signature", headers=_h("technician"),
                            json={"key": "approved_by", "signature": {"name": "X", "image": sig_img}}, timeout=30)
        assert rt.status_code == 403, rt.text

        # head can add approved_by
        rh = requests.patch(f"{API}/inspections/{iid}/signature", headers=_h("head_maintenance"),
                            json={"key": "approved_by", "signature": {"name": "Kepala", "image": sig_img}}, timeout=30)
        assert rh.status_code == 200, rh.text
        got2 = requests.get(f"{API}/inspections/{iid}", headers=_h("head_maintenance"), timeout=30).json()
        assert got2["signatures"]["approved_by"]["name"] == "Kepala"
    finally:
        requests.delete(f"{API}/inspections/{iid}", headers=_h("admin"), timeout=30)


# =========================================================================
# (D) ECR CRUD + PDF filename
# =========================================================================
_ecr_ctx = {}


def test_ecr_create_list_get():
    payload = {
        "report_type": "ECR",
        "technician": "Budi", "site_name": "TEST_ECR_Site", "unit_no": "U-1",
        "job_number": "TEST-ECR-1", "report_date": "2026-03-04",
        "working_details": "Cleaning brake", "ec": "-", "action": "Cleaned",
        "cause": "Dust", "solution": "Clean regularly", "work_status": "Closed",
        "billing": "Free", "signatures": {},
        "status": "draft",
    }
    r = requests.post(f"{API}/reports", headers=_h("technician"), json=payload, timeout=30)
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["report_type"] == "ECR"
    assert doc["site_name"] == "TEST_ECR_Site"
    assert "id" in doc
    _ecr_ctx["id"] = doc["id"]

    # list?type=ECR contains it
    lst = requests.get(f"{API}/reports?type=ECR", headers=_h("technician"), timeout=30)
    assert lst.status_code == 200
    ids = [d["id"] for d in lst.json()]
    assert doc["id"] in ids

    # GET single
    g = requests.get(f"{API}/reports/{doc['id']}", headers=_h("technician"), timeout=30)
    assert g.status_code == 200
    assert g.json()["working_details"] == "Cleaning brake"


def test_ecr_edit_draft_ok_and_forbid_after_submit():
    rid = _ecr_ctx["id"]
    # edit draft
    upd = requests.put(f"{API}/reports/{rid}", headers=_h("technician"),
                       json={"technician": "Budi Edited", "site_name": "TEST_ECR_Site",
                             "unit_no": "U-1", "job_number": "TEST-ECR-1",
                             "report_date": "2026-03-04", "working_details": "Edited",
                             "ec": "-", "action": "-", "cause": "-", "solution": "-",
                             "work_status": "Closed", "billing": "Free", "signatures": {}},
                       timeout=30)
    assert upd.status_code == 200, upd.text
    assert upd.json()["working_details"] == "Edited"

    # move to submitted
    st = requests.patch(f"{API}/reports/{rid}/status", headers=_h("technician"),
                       json={"status": "submitted"}, timeout=30)
    assert st.status_code == 200

    # now edit forbidden
    upd2 = requests.put(f"{API}/reports/{rid}", headers=_h("technician"),
                        json={"working_details": "should fail"}, timeout=30)
    assert upd2.status_code == 403, upd2.text


def test_ecr_signature_role_gating():
    rid = _ecr_ctx["id"]
    sig = {"name": "Sari", "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="}
    # supervisor -> checker OK
    r1 = requests.patch(f"{API}/reports/{rid}/signature", headers=_h("supervisor"),
                       json={"key": "checker", "signature": sig}, timeout=30)
    assert r1.status_code == 200, r1.text
    # technician -> approver 403
    r2 = requests.patch(f"{API}/reports/{rid}/signature", headers=_h("technician"),
                       json={"key": "approver", "signature": sig}, timeout=30)
    assert r2.status_code == 403, r2.text
    # head -> approver OK
    r3 = requests.patch(f"{API}/reports/{rid}/signature", headers=_h("head_maintenance"),
                       json={"key": "approver", "signature": sig}, timeout=30)
    assert r3.status_code == 200, r3.text


def test_ecr_status_approved_downgrade_only_head():
    rid = _ecr_ctx["id"]
    # move to checked then approved
    requests.patch(f"{API}/reports/{rid}/status", headers=_h("supervisor"),
                   json={"status": "checked"}, timeout=30)
    ap = requests.patch(f"{API}/reports/{rid}/status", headers=_h("head_maintenance"),
                       json={"status": "approved"}, timeout=30)
    assert ap.status_code == 200

    # supervisor downgrade -> 403
    r = requests.patch(f"{API}/reports/{rid}/status", headers=_h("supervisor"),
                       json={"status": "checked"}, timeout=30)
    assert r.status_code == 403, r.text
    # head downgrade -> 200
    r2 = requests.patch(f"{API}/reports/{rid}/status", headers=_h("head_maintenance"),
                       json={"status": "draft"}, timeout=30)
    assert r2.status_code == 200


def test_ecr_pdf_filename():
    rid = _ecr_ctx["id"]
    _t = requests.get(f"{API}/reports/{rid}/pdf-token", headers=_h("technician"), timeout=30).json()["token"]
    p = requests.get(f"{API}/reports/{rid}/pdf?auth={_t}", timeout=60)
    assert p.status_code == 200, p.text
    assert p.headers["content-type"].startswith("application/pdf")
    assert p.content[:4] == b"%PDF"
    cd = p.headers.get("content-disposition", "")
    m = re.search(r'filename="?([^";]+)"?', cd)
    assert m, cd
    fname = m.group(1)
    assert fname.startswith("ECR-"), fname
    assert re.match(r"ECR-\d{8}-", fname), fname
    assert fname.endswith(".pdf")


def test_ecr_delete_by_owner():
    rid = _ecr_ctx["id"]
    d = requests.delete(f"{API}/reports/{rid}", headers=_h("technician"), timeout=30)
    assert d.status_code == 200
    g = requests.get(f"{API}/reports/{rid}", headers=_h("technician"), timeout=30)
    assert g.status_code == 404


# =========================================================================
# (E) HOR CRUD + PDF filename
# =========================================================================
_hor_ctx = {}


def test_hor_create():
    payload = {
        "report_type": "HOR",
        "site_name": "TEST_HOR_Site", "job_number": "TEST-HOR-1",
        "report_date": "2026-04-05", "lift_number": "H1",
        "parts_replaced": [
            {"name": "Roller", "qty": 4, "before_photo_file_id": None, "after_photo_file_id": None}
        ],
        "parts_handover": [{"name": "Old Roller", "qty": 4}],
        "parts_returned": [{"name": "Damaged", "qty": 1}],
        "signatures": {"fujitec_rep": {}, "customer": {}},
        "status": "draft",
    }
    r = requests.post(f"{API}/reports", headers=_h("technician"), json=payload, timeout=30)
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["report_type"] == "HOR"
    assert len(doc["parts_replaced"]) == 1
    _hor_ctx["id"] = doc["id"]

    # list?type=HOR
    lst = requests.get(f"{API}/reports?type=HOR", headers=_h("technician"), timeout=30)
    ids = [d["id"] for d in lst.json()]
    assert doc["id"] in ids


def test_hor_signature_keys():
    rid = _hor_ctx["id"]
    sig = {"name": "Fj Rep", "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="}
    r1 = requests.patch(f"{API}/reports/{rid}/signature", headers=_h("technician"),
                       json={"key": "fujitec_rep", "signature": sig}, timeout=30)
    assert r1.status_code == 200, r1.text
    r2 = requests.patch(f"{API}/reports/{rid}/signature", headers=_h("customer"),
                       json={"key": "customer", "signature": sig}, timeout=30)
    assert r2.status_code == 200, r2.text


def test_hor_pdf_filename():
    rid = _hor_ctx["id"]
    _t = requests.get(f"{API}/reports/{rid}/pdf-token", headers=_h("technician"), timeout=30).json()["token"]
    p = requests.get(f"{API}/reports/{rid}/pdf?auth={_t}", timeout=60)
    assert p.status_code == 200
    assert p.headers["content-type"].startswith("application/pdf")
    cd = p.headers.get("content-disposition", "")
    m = re.search(r'filename="?([^";]+)"?', cd)
    assert m
    fname = m.group(1)
    assert fname.startswith("HOR-"), fname
    assert re.match(r"HOR-\d{8}-", fname), fname
    assert fname.endswith(".pdf")

    # cleanup
    requests.delete(f"{API}/reports/{rid}", headers=_h("admin"), timeout=30)


# =========================================================================
# Invalid report_type
# =========================================================================
def test_invalid_report_type_returns_400():
    r = requests.post(f"{API}/reports", headers=_h("technician"),
                      json={"report_type": "XYZ", "site_name": "x"}, timeout=30)
    assert r.status_code == 400, r.text
