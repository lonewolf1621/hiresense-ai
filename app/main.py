from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from starlette.concurrency import run_in_threadpool
from typing import Optional, List, Dict
import uvicorn
import os
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import uuid
import secrets
import threading

from config.firebase_config import db, storage_bucket
from app.services.firestore_service import FirestoreService
from app.services.cloud_storage_service import CloudStorageService
from app.services import matcher, job_feeds
from app import admin
import time as _time
from fastapi import Request

# ============= CONFIG =============
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # No hard-coded fallback: tokens are signed with a random per-process key,
    # so they stop working after a restart. Set SECRET_KEY in production.
    SECRET_KEY = secrets.token_urlsafe(32)
    print("[CONFIG] SECRET_KEY not set; using a random key for this process")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

FIREBASE_AVAILABLE = db is not None
print(f"Firebase Available: {FIREBASE_AVAILABLE}")

# Without Firebase, accounts live in memory (cleared on restart) but passwords
# are still hashed and checked, so the demo behaves like the real thing.
_DEMO_USERS: Dict[str, Dict] = {}
_DEMO_LOCK = threading.Lock()

ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS",
    "https://hiresense-ai-vishal.streamlit.app,http://localhost:8501,http://127.0.0.1:8501",
).split(",") if o.strip()]

# Password hashing – bcrypt requires passwords ≤ 72 bytes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def safe_hash_password(password: str) -> str:
    """Hash password after truncating to 72 bytes if necessary."""
    try:
        # Encode to UTF-8 and limit to 72 bytes
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            password = password_bytes.decode('utf-8', errors='ignore')
        
        return pwd_context.hash(password)
    except Exception as e:
        print(f"[ERROR] Hash password failed: {e}")
        raise

def safe_verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with 72-byte limit."""
    try:
        if isinstance(plain_password, str):
            password_bytes = plain_password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            plain_password = password_bytes.decode('utf-8', errors='ignore')
        
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"[ERROR] Verify password failed: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Dict:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": sub}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# FastAPI App
app = FastAPI(
    title="HireSense API",
    version="1.0.0",
    description="Smart Resume and Job Matching Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def _metrics(request: Request, call_next):
    start = _time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        admin.record_request(request.method, getattr(route, "path", request.url.path), status,
                             (_time.perf_counter() - start) * 1000)


def _demo_user_by_id(uid: str):
    return next((u for u in _DEMO_USERS.values() if u["id"] == uid), None)


# ============= MODELS =============
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field("", max_length=30)

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    name: str
    phone: str
    experience: int
    skills: List[str]
    targetRoles: List[str]
    targetCities: List[str]
    targetCompanies: List[str]

class JobApplication(BaseModel):
    jobId: str
    jobTitle: str
    company: str
    matchScore: Optional[float] = None
    url: Optional[str] = ""
    location: Optional[str] = ""
    source: Optional[str] = ""
    status: Optional[str] = "Applied"
    notes: Optional[str] = ""

class JobSearch(BaseModel):
    keyword: str = Field(..., min_length=2, max_length=100)
    location: Optional[str] = Field("", max_length=100, description='Optional: city or region, "Remote", or empty for anywhere')
    source: Optional[str] = Field(None, description="Optional: Remotive, Arbeitnow or Adzuna; empty for all")
    country: Optional[str] = Field(None, description="Optional country code: gb, in, us, ca, ie, de, nl, fr, au, sg")

# ============= DEPENDENCY =============
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Require a valid 'Authorization: Bearer <token>' header."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated",
                            headers={"WWW-Authenticate": "Bearer"})
    payload = verify_token(authorization.split(" ", 1)[1].strip())
    if not FIREBASE_AVAILABLE:
        u = _demo_user_by_id(payload.get("user_id"))
        if not u:
            raise HTTPException(status_code=401, detail="Account no longer exists")
        if u.get("locked"):
            raise HTTPException(status_code=403, detail="Account suspended by the administrator")
    return payload

# ============= AUTH ROUTES =============
@app.post("/api/auth/register")
async def register(user: UserRegister):
    """Register a new user account."""
    admin.feature_on("registration_enabled")
    print("[REGISTER] Attempt")
    try:
        user_id = str(uuid.uuid4())
        print(f"[REGISTER] Generated user_id: {user_id}")
        
        # Hash password with 72-byte safety
        hashed = safe_hash_password(user.password)
        print(f"[REGISTER] Password hashed successfully")

        if FIREBASE_AVAILABLE:
            print(f"[REGISTER] Checking if email exists in Firebase")
            exists = list(db.collection('users').where('email', '==', user.email).stream())
            if exists:
                print(f"[REGISTER] Email already exists")
                raise HTTPException(status_code=400, detail="Email already exists")
            
            print(f"[REGISTER] Creating user in Firebase")
            db.collection('users').document(user_id).set({
                'email': user.email,
                'name': user.name,
                'phone': user.phone,
                'password': hashed,
                'profile': {
                    'experience': 0,
                    'skills': [],
                    'targetRoles': [],
                    'targetCities': [],
                    'targetCompanies': [],
                    'createdAt': datetime.now()
                }
            })
            print(f"[REGISTER] User created in Firebase")
        else:
            key = user.email.lower()
            with _DEMO_LOCK:
                if key in _DEMO_USERS:
                    raise HTTPException(status_code=400, detail="Email already exists")
                _DEMO_USERS[key] = {"id": user_id, "name": user.name, "email": user.email,
                                    "phone": user.phone, "password": hashed,
                                    "created": datetime.utcnow().isoformat(timespec="seconds"),
                                    "locked": False, "last_login": None}
            print(f"[REGISTER] Created in-memory demo user")

        token = create_access_token({"sub": user_id})
        admin.log_event("user_registered", email=user.email)
        
        return {
            "message": "User registered successfully",
            "user_id": user_id,
            "name": user.name,
            "email": user.email,
            "access_token": token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        print(f"[REGISTER] HTTPException: {e.detail}")
        raise
    except Exception as e:
        print(f"[REGISTER] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
async def login(user: UserLogin):
    """Login with email and password."""
    try:
        if FIREBASE_AVAILABLE:
            print(f"[LOGIN] Checking Firebase")
            docs = list(db.collection('users').where('email', '==', user.email).stream())
            if not docs:
                print(f"[LOGIN] User not found")
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            udoc = docs[0]
            udata = udoc.to_dict()
            uid = udoc.id
            
            print(f"[LOGIN] Verifying password")
            if not safe_verify_password(user.password, udata.get('password', '')):
                print(f"[LOGIN] Password incorrect")
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            print(f"[LOGIN] Login successful")
        else:
            udata = _DEMO_USERS.get(user.email.lower())
            if not udata or not safe_verify_password(user.password, udata["password"]):
                admin.log_event("login_failed", email=user.email.lower())
                raise HTTPException(status_code=401, detail="Invalid credentials")
            if udata.get("locked"):
                admin.log_event("login_blocked_suspended", email=udata["email"])
                raise HTTPException(status_code=403, detail="Account suspended by the administrator")
            udata["last_login"] = datetime.utcnow().isoformat(timespec="seconds")
            uid = udata["id"]
            admin.log_event("login_success", email=udata["email"])

        token = create_access_token({"sub": uid})
        return {
            "message": "Login successful",
            "user_id": uid,
            "name": udata.get('name', 'User'),
            "email": udata.get('email'),
            "access_token": token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[LOGIN] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============= PROFILE ROUTES =============
@app.get("/api/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile."""
    try:
        uid = current_user['user_id']
        print(f"[PROFILE] Getting profile for {uid}")
        
        if not FIREBASE_AVAILABLE:
            demo = next((u for u in _DEMO_USERS.values() if u["id"] == uid), None)
            if demo:
                return {"email": demo["email"], "name": demo["name"], "phone": demo["phone"],
                        "profile": {"experience": 0, "skills": [], "targetRoles": [],
                                    "targetCities": [], "targetCompanies": []}}
        data = FirestoreService.get_user_profile(uid)
        if not data:
            print(f"[PROFILE] Returning demo profile")
            return {
                'email': 'demo@example.com',
                'name': 'Demo User',
                'phone': '+91 9999999999',
                'profile': {
                    'experience': 0,
                    'skills': [],
                    'targetRoles': [],
                    'targetCities': [],
                    'targetCompanies': []
                }
            }
        return data
    except Exception as e:
        print(f"[PROFILE] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/profile")
async def update_profile(profile: UserProfile, current_user: dict = Depends(get_current_user)):
    """Update user profile."""
    try:
        uid = current_user['user_id']
        print(f"[PROFILE] Updating profile for {uid}")
        
        success = FirestoreService.update_user_profile(uid, profile.dict())
        if success:
            return {"message": "Profile updated successfully"}
        raise HTTPException(status_code=500, detail="Update failed")
    except Exception as e:
        print(f"[PROFILE] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= RESUME ROUTES =============
@app.post("/api/resumes/upload")
async def upload_resume(
    file: UploadFile = File(...),
    name: str = Form(...),
    isPrimary: bool = Form(False),
    current_user: dict = Depends(get_current_user)
):
    """Upload resume file."""
    try:
        uid = current_user['user_id']
        print(f"[RESUME] Uploading for {uid}: {file.filename}")
        
        contents = await file.read()
        url = CloudStorageService.upload_resume_bytes(uid, contents, file.filename)
        if not url:
            url = f"https://storage.example.com/{file.filename}"
        
        rid = str(uuid.uuid4())
        FirestoreService.save_resume(uid, rid, {'name': name, 'gcsUrl': url, 'isPrimary': isPrimary})
        
        return {"message": "Resume uploaded", "resume_id": rid, "url": url}
    except Exception as e:
        print(f"[RESUME] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumes")
async def get_resumes(current_user: dict = Depends(get_current_user)):
    """Get all user resumes."""
    try:
        uid = current_user['user_id']
        print(f"[RESUME] Getting resumes for {uid}")
        resumes = FirestoreService.get_user_resumes(uid)
        return {"resumes": resumes if resumes else []}
    except Exception as e:
        print(f"[RESUME] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/resumes/{resume_id}")
async def delete_resume(resume_id: str, current_user: dict = Depends(get_current_user)):
    """Delete resume."""
    try:
        uid = current_user['user_id']
        print(f"[RESUME] Deleting {resume_id}")
        ok = CloudStorageService.delete_resume(uid, resume_id)
        if ok:
            return {"message": "Resume deleted"}
        raise HTTPException(status_code=500, detail="Delete failed")
    except Exception as e:
        print(f"[RESUME] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= JOB ROUTES =============
# Jobs seen in recent searches, so a job can be fetched again by id.
_JOB_INDEX: Dict[str, Dict] = {}
# Applications per user when Firebase is not configured (cleared on restart).
_DEMO_APPS: Dict[str, Dict[str, Dict]] = {}
APPLICATION_STATUSES = ["Saved", "Applied", "Interview", "Offer", "Rejected"]


@app.get("/api/jobs/sources")
async def job_sources():
    """Which live job feeds are enabled."""
    return {"sources": job_feeds.available_sources(),
            "countries": [{"code": c, "name": n} for c, (n, _) in job_feeds.COUNTRIES.items()]}


@app.post("/api/jobs/search")
async def search_jobs(search: JobSearch, current_user: dict = Depends(get_current_user)):
    """Search live job feeds; every job includes its full description and original link."""
    admin.feature_on("job_search_enabled")
    result = await run_in_threadpool(job_feeds.search, search.keyword, search.location,
                                     search.source, search.country)
    for job in result["jobs"]:
        _JOB_INDEX[job["id"]] = job
    if len(_JOB_INDEX) > 5000:  # keep memory bounded on a small instance
        for k in list(_JOB_INDEX)[:-2000]:
            _JOB_INDEX.pop(k, None)
    return result


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, current_user: dict = Depends(get_current_user)):
    """A job from a recent search, with its full description."""
    job = _JOB_INDEX.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found (search again to refresh)")
    return job


# ============= APPLICATION ROUTES =============
@app.post("/api/applications")
async def apply_job(application: JobApplication, current_user: dict = Depends(get_current_user)):
    """Track a job you applied to (or saved). Applying itself happens on the job's own site."""
    uid = current_user["user_id"]
    aid = str(uuid.uuid4())
    record = application.dict()
    if record.get("status") not in APPLICATION_STATUSES:
        record["status"] = "Applied"
    record.update({"id": aid,
                   "appliedDate": datetime.utcnow().strftime("%Y-%m-%d")})
    if FIREBASE_AVAILABLE:
        if not FirestoreService.save_job_application(uid, aid, record):
            raise HTTPException(status_code=500, detail="Save failed")
    else:
        with _DEMO_LOCK:
            apps = _DEMO_APPS.setdefault(uid, {})
            for existing in apps.values():
                if existing["jobId"] == record["jobId"]:
                    return {"message": "Already tracked", "application_id": existing["id"]}
            apps[aid] = record
    return {"message": "Application saved", "application_id": aid}


@app.get("/api/applications")
async def get_applications(current_user: dict = Depends(get_current_user)):
    """Your tracked applications, newest first."""
    uid = current_user["user_id"]
    if FIREBASE_AVAILABLE:
        apps = FirestoreService.get_user_applications(uid) or []
    else:
        apps = list(_DEMO_APPS.get(uid, {}).values())
    apps.sort(key=lambda a: a.get("appliedDate", ""), reverse=True)
    return {"applications": apps, "statuses": APPLICATION_STATUSES}


@app.put("/api/applications/{app_id}")
async def update_application(app_id: str, status: str, current_user: dict = Depends(get_current_user)):
    """Change an application's status (Saved, Applied, Interview, Offer, Rejected)."""
    if status not in APPLICATION_STATUSES:
        raise HTTPException(status_code=422, detail=f"Status must be one of {APPLICATION_STATUSES}")
    uid = current_user["user_id"]
    if FIREBASE_AVAILABLE:
        if not FirestoreService.update_application_status(uid, app_id, status):
            raise HTTPException(status_code=500, detail="Update failed")
    else:
        app_rec = _DEMO_APPS.get(uid, {}).get(app_id)
        if not app_rec:
            raise HTTPException(status_code=404, detail="Application not found")
        app_rec["status"] = status
    return {"message": "Updated", "status": status}


@app.delete("/api/applications/{app_id}")
async def delete_application(app_id: str, current_user: dict = Depends(get_current_user)):
    uid = current_user["user_id"]
    if FIREBASE_AVAILABLE:
        raise HTTPException(status_code=501, detail="Not supported with Firebase yet")
    if not _DEMO_APPS.get(uid, {}).pop(app_id, None):
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Deleted"}

# ============= MATCHING =============
class MatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, max_length=30000)
    job_description: str = Field(..., min_length=50, max_length=30000)


@app.on_event("startup")
async def warm_matcher():
    """Start loading the embedding model so the first match request is fast."""
    matcher.warm_up()


@app.post("/api/match")
async def match_cv_to_job(req: MatchRequest):
    """Score a CV against a job description.

    Returns an overall match score, skill coverage, semantic coverage,
    matched/missing skills, and for the top requirements the CV line that
    best supports each one (retrieved with FAISS over MiniLM embeddings).
    """
    admin.feature_on("matching_enabled")
    try:
        return await run_in_threadpool(matcher.match, req.resume_text, req.job_description)
    except Exception as e:
        print(f"[MATCH] ERROR: {e}")
        raise HTTPException(status_code=500, detail="Matching failed")

MAX_CV_BYTES = 5 * 1024 * 1024


def extract_cv_text(filename: str, data: bytes) -> str:
    """Text from a PDF, DOCX or TXT CV."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        import io
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    if name.endswith(".docx"):
        import io
        import docx
        return "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    raise HTTPException(status_code=415, detail="Upload a PDF, DOCX or TXT file")


@app.post("/api/match/file")
async def match_cv_file_to_job(
    file: UploadFile = File(..., description="CV as PDF, DOCX or TXT (max 5 MB)"),
    job_description: str = Form(..., min_length=50, max_length=30000),
):
    """Same as /api/match, but takes the CV as an uploaded file."""
    admin.feature_on("matching_enabled")
    data = await file.read()
    if len(data) > MAX_CV_BYTES:
        raise HTTPException(status_code=413, detail="CV file larger than 5 MB")
    try:
        text = extract_cv_text(file.filename, data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[MATCH] Could not read {file.filename}: {e}")
        raise HTTPException(status_code=422, detail="Could not read text from this file")
    if len(text.strip()) < 50:
        raise HTTPException(status_code=422, detail="Too little text found in the CV (is it a scanned image?)")
    result = await run_in_threadpool(matcher.match, text, job_description)
    result["cv_characters"] = len(text)
    return result


MAX_RANK_FILES = 10


def _rank(cvs: List[Dict[str, str]], job_description: str) -> Dict:
    """Score every CV against one job and return them best first."""
    ranked = []
    for cv in cvs:
        r = matcher.match(cv["text"], job_description, top_k=3)
        ranked.append({
            "name": cv["name"],
            "match_score": r["match_score"],
            "skill_score": r["skill_score"],
            "semantic_score": r["semantic_score"],
            "matched_skills": r["matched_skills"],
            "missing_skills": r["missing_skills"],
            "top_evidence": r["evidence"][:3],
        })
    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    for i, item in enumerate(ranked, 1):
        item["rank"] = i
    return {"count": len(ranked), "ranking": ranked, "method": matcher.embedder.status}


class RankRequest(BaseModel):
    job_description: str = Field(..., min_length=50, max_length=30000)
    resumes: List[Dict[str, str]] = Field(
        ..., min_length=1, max_length=MAX_RANK_FILES,
        description='List of {"name": "...", "text": "..."} (1–10 CVs)',
    )


@app.post("/api/match/rank")
async def rank_cvs(req: RankRequest):
    """Rank several CVs (as text) against one job description."""
    admin.feature_on("matching_enabled")
    cvs = []
    for i, cv in enumerate(req.resumes, 1):
        text = (cv.get("text") or "").strip()
        if len(text) < 50:
            raise HTTPException(status_code=422, detail=f"CV {i} has fewer than 50 characters")
        if len(text) > 30000:
            raise HTTPException(status_code=422, detail=f"CV {i} is longer than 30000 characters")
        cvs.append({"name": cv.get("name") or f"CV {i}", "text": text})
    return await run_in_threadpool(_rank, cvs, req.job_description)


@app.post("/api/match/rank/files")
async def rank_cv_files(
    files: List[UploadFile] = File(..., description="2–10 CVs as PDF, DOCX or TXT (max 5 MB each)"),
    job_description: str = Form(..., min_length=50, max_length=30000),
):
    """Rank several uploaded CVs against one job description, best match first."""
    admin.feature_on("matching_enabled")
    if len(files) > MAX_RANK_FILES:
        raise HTTPException(status_code=422, detail=f"Upload at most {MAX_RANK_FILES} CVs")
    cvs, skipped = [], []
    for f in files:
        data = await f.read()
        if len(data) > MAX_CV_BYTES:
            skipped.append({"name": f.filename, "reason": "larger than 5 MB"})
            continue
        try:
            text = extract_cv_text(f.filename, data)
        except HTTPException as e:
            skipped.append({"name": f.filename, "reason": e.detail})
            continue
        except Exception:
            skipped.append({"name": f.filename, "reason": "could not read text"})
            continue
        if len(text.strip()) < 50:
            skipped.append({"name": f.filename, "reason": "too little text (scanned image?)"})
            continue
        cvs.append({"name": f.filename, "text": text[:30000]})
    if not cvs:
        raise HTTPException(status_code=422, detail={"message": "No readable CVs", "skipped": skipped})
    result = await run_in_threadpool(_rank, cvs, job_description)
    result["skipped"] = skipped
    return result

# ============= ADMIN (owner only) =============
class AdminSettings(BaseModel):
    maintenance_banner: Optional[str] = Field(None, max_length=300)
    registration_enabled: Optional[bool] = None
    matching_enabled: Optional[bool] = None
    job_search_enabled: Optional[bool] = None


@app.get("/api/status")
async def public_status():
    """Public: maintenance banner and which features are on (used by the front end)."""
    return {k: v for k, v in admin.settings.items()}


@app.get("/api/admin/stats", dependencies=[Depends(admin.require_admin)])
async def admin_stats():
    users = list(_DEMO_USERS.values())
    apps = [a for per_user in _DEMO_APPS.values() for a in per_user.values()]
    by_status: Dict[str, int] = {}
    for a in apps:
        by_status[a.get("status", "?")] = by_status.get(a.get("status", "?"), 0) + 1
    return {
        "uptime_seconds": admin.uptime_seconds(),
        "storage": "firebase" if FIREBASE_AVAILABLE else "in-memory (resets on restart)",
        "matcher": matcher.embedder.status,
        "users": {"total": len(users), "suspended": sum(bool(u.get("locked")) for u in users)},
        "applications": {"total": len(apps), "by_status": by_status},
        "events": admin.event_counts(),
        "endpoints": admin.endpoint_stats(),
        "job_feeds": job_feeds.available_sources(),
    }


@app.get("/api/admin/users", dependencies=[Depends(admin.require_admin)])
async def admin_users():
    if FIREBASE_AVAILABLE:
        raise HTTPException(status_code=501, detail="User management for Firebase is done in the Firebase console")
    return {"users": [{"email": u["email"], "name": u["name"], "created": u.get("created"),
                       "last_login": u.get("last_login"), "suspended": bool(u.get("locked")),
                       "applications": len(_DEMO_APPS.get(u["id"], {}))} for u in _DEMO_USERS.values()]}


def _admin_find(email: str) -> Dict:
    u = _DEMO_USERS.get(email.lower())
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


@app.post("/api/admin/users/{email}/suspend", dependencies=[Depends(admin.require_admin)])
async def admin_suspend(email: str):
    _admin_find(email)["locked"] = True
    admin.log_event("admin_suspended_user", email=email.lower())
    return {"ok": True}


@app.post("/api/admin/users/{email}/unsuspend", dependencies=[Depends(admin.require_admin)])
async def admin_unsuspend(email: str):
    _admin_find(email)["locked"] = False
    admin.log_event("admin_unsuspended_user", email=email.lower())
    return {"ok": True}


@app.delete("/api/admin/users/{email}", dependencies=[Depends(admin.require_admin)])
async def admin_delete_user(email: str):
    u = _admin_find(email)
    with _DEMO_LOCK:
        _DEMO_USERS.pop(email.lower(), None)
        _DEMO_APPS.pop(u["id"], None)
    admin.log_event("admin_deleted_user", email=email.lower())
    return {"ok": True}


@app.get("/api/admin/logs", dependencies=[Depends(admin.require_admin)])
async def admin_logs(kind: str = "events", limit: int = 100):
    if kind not in ("events", "requests"):
        raise HTTPException(status_code=422, detail="kind must be 'events' or 'requests'")
    return {"kind": kind, "items": admin.recent(min(max(limit, 1), 300), kind)}


@app.get("/api/admin/settings", dependencies=[Depends(admin.require_admin)])
async def admin_get_settings():
    return admin.settings


@app.put("/api/admin/settings", dependencies=[Depends(admin.require_admin)])
async def admin_put_settings(body: AdminSettings):
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    admin.settings.update(changes)
    admin.log_event("admin_changed_settings", **{k: str(v) for k, v in changes.items()})
    return admin.settings


@app.post("/api/admin/clear-demo-data", dependencies=[Depends(admin.require_admin)])
async def admin_clear(confirm: str = ""):
    if confirm != "DELETE":
        raise HTTPException(status_code=422, detail="Pass ?confirm=DELETE to remove all demo users and applications")
    with _DEMO_LOCK:
        n = len(_DEMO_USERS)
        _DEMO_USERS.clear()
        _DEMO_APPS.clear()
    admin.reset_metrics()
    admin.log_event("admin_cleared_demo_data", users_removed=n)
    return {"ok": True, "users_removed": n}


# ============= MISC ROUTES =============
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "firebase": FIREBASE_AVAILABLE,
        "matcher": matcher.embedder.status,
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HireSense API",
        "version": "1.0.0",
        "docs": "/docs",
        "firebase": FIREBASE_AVAILABLE
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)