from dotenv import load_dotenv
from pathlib import Path
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import logging
import uuid
import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Annotated, Any

import bcrypt
import jwt
import requests
import httpx
from bson import ObjectId
from fastapi import FastAPI, APIRouter, Request, HTTPException, Depends, UploadFile, File, Header, Query
from fastapi.responses import Response, StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, BeforeValidator, EmailStr

from checklist_data import get_checklist, SECTIONS
from pdf_report import build_sir_pdf
from email_service import send_email, spare_change_html

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Fujitec SIR")
api_router = APIRouter(prefix="/api")

JWT_ALGORITHM = "HS256"
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "fujitec-sir"
storage_key = None

ROLES = ["admin", "technician", "supervisor", "head_maintenance", "sales", "inventory", "customer"]
OWNER_EMAIL = os.environ.get("OWNER_EMAIL", "").lower()
AUTH_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"

MIME_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp", "heic": "image/heic",
}

# ---------------------------------------------------------------------------
# Mongo helpers
# ---------------------------------------------------------------------------
PyObjectId = Annotated[str, BeforeValidator(str)]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key


def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = requests.put(f"{STORAGE_URL}/objects/{path}",
                        headers={"X-Storage-Key": key, "Content-Type": content_type},
                        data=data, timeout=120)
    resp.raise_for_status()
    return resp.json()


def get_object(path: str):
    key = init_storage()
    resp = requests.get(f"{STORAGE_URL}/objects/{path}",
                        headers={"X-Storage-Key": key}, timeout=60)
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


# ---------------------------------------------------------------------------
# Auth utilities
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {"sub": user_id, "email": email, "role": role,
               "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_roles(*roles):
    async def checker(user: dict = Depends(get_current_user)):
        if user["role"] not in roles and user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Not authorized for this action")
        return user
    return checker


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class RegisterInput(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "technician"


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class Point(BaseModel):
    index: int
    measurement: str = ""
    photo_file_id: Optional[str] = None


class ChecklistItemResult(BaseModel):
    no: int
    section: str
    description: str
    photo_points: int = 0
    judgment: Optional[str] = None  # good | replaced | damage | none
    remark: str = ""
    points: List[Point] = []


class SparePart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    quantity: str = ""
    sales_status: str = "pending"        # pending | offered
    customer_po_status: str = "pending"  # pending | po_issued
    inventory_status: str = "pending"    # pending | available | ordering | no_stock | discontinued
    maintenance_status: str = "pending"  # pending | replaced
    note: str = ""


class Signature(BaseModel):
    name: str = ""
    image: str = ""  # data URL
    signed_at: Optional[str] = None


class Signatures(BaseModel):
    issued_by: Signature = Signature()
    customer: Signature = Signature()
    checked_by: Signature = Signature()
    approved_by: Signature = Signature()


class InspectionInput(BaseModel):
    job_number: str
    site_name: str
    inspection_date: str
    time_from: str
    time_to: str
    serviced_by: str
    total_units: int = 0
    lift_number: str
    checklist_type: str  # 1M | 3M | 12M
    items: List[ChecklistItemResult] = []
    global_remark: str = ""
    spare_parts: List[SparePart] = []
    signatures: Signatures = Signatures()
    status: str = "draft"  # draft | submitted | checked | approved


class SparePartStatusUpdate(BaseModel):
    field: str  # sales_status | customer_po_status | inventory_status | maintenance_status | note
    value: str


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@api_router.post("/auth/register")
async def register(data: RegisterInput):
    email = data.email.lower()
    if data.role not in ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    doc = {
        "email": email,
        "password_hash": hash_password(data.password),
        "name": data.name,
        "role": data.role,
        "created_at": now_iso(),
    }
    res = await db.users.insert_one(doc)
    uid = str(res.inserted_id)
    token = create_access_token(uid, email, data.role)
    return {"access_token": token, "user": {"id": uid, "email": email, "name": data.name, "role": data.role}}


@api_router.post("/auth/login")
async def login(data: LoginInput, request: Request):
    email = data.email.lower()
    ident = f"{request.client.host}:{email}"
    attempt = await db.login_attempts.find_one({"identifier": ident})
    if attempt and attempt.get("count", 0) >= 5:
        locked_until = attempt.get("locked_until")
        if locked_until and datetime.fromisoformat(locked_until) > datetime.now(timezone.utc):
            raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
    user = await db.users.find_one({"email": email})
    if not user or not user.get("password_hash") or not verify_password(data.password, user["password_hash"]):
        await db.login_attempts.update_one(
            {"identifier": ident},
            {"$inc": {"count": 1},
             "$set": {"locked_until": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()}},
            upsert=True)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await db.login_attempts.delete_one({"identifier": ident})
    uid = str(user["_id"])
    token = create_access_token(uid, email, user["role"])
    return {"access_token": token, "user": {"id": uid, "email": email, "name": user["name"], "role": user["role"]}}


@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


class GoogleSessionInput(BaseModel):
    session_id: str


@api_router.post("/auth/google-session")
async def google_session(data: GoogleSessionInput):
    # Exchange Emergent session_id for profile, then mint our own JWT.
    try:
        async with httpx.AsyncClient(timeout=30) as hc:
            resp = await hc.get(AUTH_SESSION_URL, headers={"X-Session-ID": data.session_id})
        resp.raise_for_status()
        profile = resp.json()
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Google session")
    email = profile["email"].lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        uid = str(existing["_id"])
        role = existing["role"]
    else:
        role = "admin" if email == OWNER_EMAIL else "technician"
        doc = {"email": email, "name": profile.get("name", email), "role": role,
               "picture": profile.get("picture"), "auth_provider": "google", "created_at": now_iso()}
        res = await db.users.insert_one(doc)
        uid = str(res.inserted_id)
    token = create_access_token(uid, email, role)
    return {"access_token": token, "user": {"id": uid, "email": email,
            "name": profile.get("name", email), "role": role}}


@api_router.post("/auth/logout")
async def logout(user: dict = Depends(get_current_user)):
    return {"ok": True}


# ---------------------------------------------------------------------------
# Users (admin)
# ---------------------------------------------------------------------------
@api_router.get("/users")
async def list_users(user: dict = Depends(require_roles("admin", "supervisor", "head_maintenance"))):
    users = await db.users.find({}, {"password_hash": 0}).to_list(500)
    for u in users:
        u["id"] = str(u["_id"])
        u.pop("_id", None)
    return users


@api_router.post("/users")
async def create_user(data: RegisterInput, user: dict = Depends(require_roles("admin"))):
    return await register(data)


@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, user: dict = Depends(require_roles("admin"))):
    await db.users.delete_one({"_id": ObjectId(user_id)})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Checklist master
# ---------------------------------------------------------------------------
@api_router.get("/checklist/master")
async def checklist_master(type: str = Query(...), user: dict = Depends(get_current_user)):
    if type not in ("1M", "3M", "12M"):
        raise HTTPException(status_code=400, detail="Invalid checklist type")
    return {"type": type, "sections": SECTIONS, "items": get_checklist(type)}


# ---------------------------------------------------------------------------
# Buildings (master gedung)
# ---------------------------------------------------------------------------
@api_router.get("/buildings")
async def search_buildings(q: str = Query("", ), user: dict = Depends(get_current_user)):
    query = {}
    if q:
        query = {"$or": [
            {"job_number": {"$regex": q, "$options": "i"}},
            {"site_name": {"$regex": q, "$options": "i"}},
            {"city": {"$regex": q, "$options": "i"}},
        ]}
    docs = await db.buildings.find(query, {"_id": 0}).limit(20).to_list(20)
    return docs


@api_router.get("/buildings/lookup")
async def lookup_building(job_number: str = Query(...), user: dict = Depends(get_current_user)):
    doc = await db.buildings.find_one({"job_number": {"$regex": f"^{job_number}$", "$options": "i"}}, {"_id": 0})
    return doc or {}


# ---------------------------------------------------------------------------
# Files / photo upload
# ---------------------------------------------------------------------------
@api_router.post("/upload")
async def upload(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    ext = (file.filename.split(".")[-1] if "." in file.filename else "bin").lower()
    file_id = str(uuid.uuid4())
    path = f"{APP_NAME}/uploads/{user['id']}/{file_id}.{ext}"
    data = await file.read()
    ctype = file.content_type or MIME_TYPES.get(ext, "application/octet-stream")
    result = put_object(path, data, ctype)
    await db.files.insert_one({
        "id": file_id,
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": ctype,
        "size": result.get("size", len(data)),
        "uploaded_by": user["id"],
        "is_deleted": False,
        "created_at": now_iso(),
    })
    return {"file_id": file_id, "path": result["path"]}


@api_router.get("/files/{file_id}")
async def download_file(file_id: str, auth: str = Query(None), authorization: str = Header(None)):
    record = await db.files.find_one({"id": file_id, "is_deleted": False})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    data, ctype = get_object(record["storage_path"])
    return Response(content=data, media_type=record.get("content_type", ctype))


# ---------------------------------------------------------------------------
# Inspections
# ---------------------------------------------------------------------------
def _validate_complete(data: InspectionInput):
    incomplete = [it.no for it in data.items if not it.judgment]
    if incomplete:
        raise HTTPException(status_code=400,
            detail=f"Checklist belum 100% terisi. {len(incomplete)} item belum diberi judgment. Simpan sebagai draft dulu.")


def _visible_query(user: dict):
    """Restrict list results by role."""
    if user["role"] in ("admin", "supervisor", "head_maintenance", "sales", "inventory"):
        return {}
    if user["role"] == "technician":
        return {"technician_id": user["id"]}
    if user["role"] == "customer":
        return {}  # customers can see reports (could be scoped by site later)
    return {}


@api_router.post("/inspections")
async def create_inspection(data: InspectionInput, user: dict = Depends(get_current_user)):
    if data.status == "submitted":
        _validate_complete(data)
    doc = data.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["technician_id"] = user["id"]
    doc["technician_name"] = user["name"]
    doc["created_at"] = now_iso()
    doc["updated_at"] = now_iso()
    await db.inspections.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.get("/inspections")
async def list_inspections(user: dict = Depends(get_current_user),
                           status: Optional[str] = None,
                           checklist_type: Optional[str] = None,
                           q: Optional[str] = None):
    query = _visible_query(user)
    if status:
        query["status"] = status
    if checklist_type:
        query["checklist_type"] = checklist_type
    if q:
        query["$or"] = [
            {"job_number": {"$regex": q, "$options": "i"}},
            {"site_name": {"$regex": q, "$options": "i"}},
            {"lift_number": {"$regex": q, "$options": "i"}},
        ]
    docs = await db.inspections.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    # Trim heavy fields for list
    for d in docs:
        d.pop("items", None)
        d.pop("signatures", None)
    return docs


@api_router.get("/inspections/{inspection_id}")
async def get_inspection(inspection_id: str, user: dict = Depends(get_current_user)):
    doc = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return doc


@api_router.put("/inspections/{inspection_id}")
async def update_inspection(inspection_id: str, data: InspectionInput, user: dict = Depends(get_current_user)):
    existing = await db.inspections.find_one({"id": inspection_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Inspection not found")
    # Editing rules: only draft reports may be edited, by owner or admin.
    is_owner = existing.get("technician_id") == user["id"]
    if existing.get("status") != "draft" and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Laporan yang sudah dikirim tidak dapat diedit")
    if not is_owner and user["role"] not in ("admin",):
        raise HTTPException(status_code=403, detail="Hanya teknisi pembuat yang dapat mengedit draft ini")
    if data.status == "submitted":
        _validate_complete(data)
    doc = data.model_dump()
    doc["updated_at"] = now_iso()
    doc.pop("technician_id", None)
    doc.pop("technician_name", None)
    await db.inspections.update_one({"id": inspection_id}, {"$set": doc})
    updated = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
    return updated


@api_router.patch("/inspections/{inspection_id}/status")
async def update_status(inspection_id: str, payload: dict, user: dict = Depends(get_current_user)):
    status = payload.get("status")
    if status not in ("draft", "submitted", "checked", "approved"):
        raise HTTPException(status_code=400, detail="Invalid status")
    if status == "checked" and user["role"] not in ("supervisor", "head_maintenance", "admin"):
        raise HTTPException(status_code=403, detail="Only supervisor can mark as checked")
    if status == "approved" and user["role"] not in ("head_maintenance", "admin"):
        raise HTTPException(status_code=403, detail="Only head of maintenance can approve")
    await db.inspections.update_one({"id": inspection_id}, {"$set": {"status": status, "updated_at": now_iso()}})
    return {"ok": True, "status": status}


@api_router.delete("/inspections/{inspection_id}")
async def delete_inspection(inspection_id: str, user: dict = Depends(get_current_user)):
    doc = await db.inspections.find_one({"id": inspection_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    if user["role"] not in ("admin", "supervisor", "head_maintenance") and doc.get("technician_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.inspections.delete_one({"id": inspection_id})
    return {"ok": True}


@api_router.get("/inspections/{inspection_id}/pdf")
async def inspection_pdf(inspection_id: str, auth: str = Query(None)):
    doc = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    # Pre-fetch photos for the attachment sheet.
    photos = {}
    for it in doc.get("items", []):
        for p in it.get("points", []):
            fid = p.get("photo_file_id")
            if fid and fid not in photos:
                rec = await db.files.find_one({"id": fid, "is_deleted": False})
                if rec:
                    try:
                        data, _ = get_object(rec["storage_path"])
                        photos[fid] = data
                    except Exception:
                        pass
    pdf_bytes = build_sir_pdf(doc, photos=photos)
    filename = f"SIR-{doc.get('job_number','report')}-{doc.get('lift_number','')}.pdf"
    return StreamingResponse(iter([pdf_bytes]), media_type="application/pdf",
                             headers={"Content-Disposition": f'inline; filename="{filename}"'})


# ---------------------------------------------------------------------------
# Spare parts follow-up
# ---------------------------------------------------------------------------
@api_router.get("/spare-parts")
async def list_spare_parts(user: dict = Depends(get_current_user),
                           inventory_status: Optional[str] = None,
                           only_open: bool = False):
    docs = await db.inspections.find(
        {"spare_parts.0": {"$exists": True}}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    rows = []
    for d in docs:
        for sp in d.get("spare_parts", []):
            row = dict(sp)
            row["inspection_id"] = d["id"]
            row["job_number"] = d.get("job_number")
            row["site_name"] = d.get("site_name")
            row["lift_number"] = d.get("lift_number")
            row["inspection_date"] = d.get("inspection_date")
            row["checklist_type"] = d.get("checklist_type")
            if inventory_status and row.get("inventory_status") != inventory_status:
                continue
            if only_open and row.get("maintenance_status") == "replaced":
                continue
            rows.append(row)
    return rows


@api_router.patch("/inspections/{inspection_id}/spare-parts/{spare_id}")
async def update_spare_part(inspection_id: str, spare_id: str,
                            update: SparePartStatusUpdate,
                            user: dict = Depends(get_current_user)):
    field = update.field
    allowed_by_role = {
        "sales_status": ("sales", "supervisor", "head_maintenance", "admin"),
        "customer_po_status": ("customer", "sales", "supervisor", "head_maintenance", "admin"),
        "inventory_status": ("inventory", "supervisor", "head_maintenance", "admin"),
        "maintenance_status": ("technician", "supervisor", "head_maintenance", "admin"),
        "note": tuple(ROLES),
    }
    if field not in allowed_by_role:
        raise HTTPException(status_code=400, detail="Invalid field")
    if user["role"] not in allowed_by_role[field]:
        raise HTTPException(status_code=403, detail="Not authorized for this field")
    res = await db.inspections.update_one(
        {"id": inspection_id, "spare_parts.id": spare_id},
        {"$set": {f"spare_parts.$.{field}": update.value, "updated_at": now_iso()}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Spare part not found")
    if field != "note":
        await _notify_spare_change(inspection_id, spare_id, field, update.value, user["name"])
    return {"ok": True}


SPARE_FIELD_LABELS = {
    "sales_status": "Sales / Penawaran", "customer_po_status": "Customer (PO)",
    "inventory_status": "Inventory", "maintenance_status": "Maintenance",
}
SPARE_VALUE_LABELS = {
    "pending": "Pending", "offered": "Sudah Ditawarkan", "po_issued": "PO Terbit",
    "available": "Tersedia", "ordering": "Sedang Dipesan", "no_stock": "Tidak Ada Stok",
    "discontinued": "Discontinue", "replaced": "Sudah Diganti",
}


async def _notify_spare_change(inspection_id, spare_id, field, value, changed_by):
    insp = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
    if not insp:
        return
    sp = next((s for s in insp.get("spare_parts", []) if s.get("id") == spare_id), {})
    recipients = set()
    if OWNER_EMAIL:
        recipients.add(OWNER_EMAIL)
    async for u in db.users.find({"role": {"$in": ["head_maintenance", "supervisor"]}}, {"email": 1}):
        recipients.add(u["email"])
    html = spare_change_html(insp, sp, SPARE_FIELD_LABELS.get(field, field),
                             SPARE_VALUE_LABELS.get(value, value), changed_by)
    subject = f"[SIR] Update Spare Part — {sp.get('name','')} @ {insp.get('site_name','')}"
    for r in recipients:
        await send_email(r, subject, html)


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------
@api_router.get("/dashboard/stats")
async def dashboard_stats(user: dict = Depends(get_current_user)):
    query = _visible_query(user)
    docs = await db.inspections.find(query, {"_id": 0}).to_list(2000)
    total = len(docs)
    by_status = {"draft": 0, "submitted": 0, "checked": 0, "approved": 0}
    by_type = {"1M": 0, "3M": 0, "12M": 0}
    spare_total = 0
    spare_open = 0
    inv = {"pending": 0, "available": 0, "ordering": 0, "no_stock": 0, "discontinued": 0}
    recent = []
    for d in docs:
        by_status[d.get("status", "draft")] = by_status.get(d.get("status", "draft"), 0) + 1
        if d.get("checklist_type") in by_type:
            by_type[d["checklist_type"]] += 1
        for sp in d.get("spare_parts", []):
            spare_total += 1
            if sp.get("maintenance_status") != "replaced":
                spare_open += 1
            inv[sp.get("inventory_status", "pending")] = inv.get(sp.get("inventory_status", "pending"), 0) + 1
    for d in docs[:6]:
        recent.append({k: d.get(k) for k in
                       ("id", "job_number", "site_name", "lift_number", "checklist_type",
                        "status", "inspection_date", "technician_name")})
    recent.sort(key=lambda x: x.get("inspection_date", ""), reverse=True)
    return {"total_inspections": total, "by_status": by_status, "by_type": by_type,
            "spare_total": spare_total, "spare_open": spare_open,
            "inventory_breakdown": inv, "recent": recent[:6]}


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    try:
        await db.users.create_index("email", unique=True)
        await db.login_attempts.create_index("identifier")
        await db.inspections.create_index("id", unique=True)
        await db.files.create_index("id", unique=True)
    except Exception as e:
        logger.warning(f"index creation: {e}")
    # Seed admin + demo users
    await seed_users()
    await load_buildings()
    try:
        init_storage()
        logger.info("Storage initialized")
    except Exception as e:
        logger.error(f"Storage init failed: {e}")


async def seed_users():
    seeds = [
        (os.environ.get("ADMIN_EMAIL", "admin@fujitec.com"), os.environ.get("ADMIN_PASSWORD", "admin123"), "Administrator", "admin"),
        ("teknisi@fujitec.com", "teknisi123", "Budi Teknisi", "technician"),
        ("supervisor@fujitec.com", "super123", "Sari Supervisor", "supervisor"),
        ("kepala@fujitec.com", "kepala123", "Head Maintenance", "head_maintenance"),
        ("sales@fujitec.com", "sales123", "Sales Service", "sales"),
        ("inventory@fujitec.com", "inv123", "Inventory Team", "inventory"),
        ("customer@fujitec.com", "cust123", "Customer PIC", "customer"),
    ]
    for email, pw, name, role in seeds:
        existing = await db.users.find_one({"email": email})
        if not existing:
            await db.users.insert_one({"email": email, "password_hash": hash_password(pw),
                                       "name": name, "role": role, "created_at": now_iso()})
        elif existing.get("password_hash") and not verify_password(pw, existing["password_hash"]):
            await db.users.update_one({"email": email}, {"$set": {"password_hash": hash_password(pw)}})
    # Ensure owner (Google) account exists as admin
    if OWNER_EMAIL and not await db.users.find_one({"email": OWNER_EMAIL}):
        await db.users.insert_one({"email": OWNER_EMAIL, "name": "Agus Supriyadi",
                                   "role": "admin", "auth_provider": "google", "created_at": now_iso()})


async def load_buildings():
    try:
        if await db.buildings.count_documents({}) > 0:
            return
        path = ROOT_DIR / "data_buildings.json"
        if not path.exists():
            return
        rows = json.loads(path.read_text(encoding="utf-8"))
        if rows:
            await db.buildings.insert_many(rows)
            await db.buildings.create_index("job_number")
            logger.info(f"Loaded {len(rows)} buildings")
    except Exception as e:
        logger.error(f"load_buildings failed: {e}")


@app.on_event("shutdown")
async def shutdown():
    client.close()


app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
