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
from app.services import matcher

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
    matchScore: float
    notes: Optional[str] = ""

class JobSearch(BaseModel):
    keyword: str
    location: str = "India"
    source: Optional[str] = None

# ============= DEPENDENCY =============
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Require a valid 'Authorization: Bearer <token>' header."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated",
                            headers={"WWW-Authenticate": "Bearer"})
    return verify_token(authorization.split(" ", 1)[1].strip())

# ============= AUTH ROUTES =============
@app.post("/api/auth/register")
async def register(user: UserRegister):
    """Register a new user account."""
    print(f"[REGISTER] Attempt: {user.email}")
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
                                    "phone": user.phone, "password": hashed}
            print(f"[REGISTER] Created in-memory demo user")

        token = create_access_token({"sub": user_id})
        print(f"[REGISTER] Token created successfully")
        
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
    print(f"[LOGIN] Attempt: {user.email}")
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
                raise HTTPException(status_code=401, detail="Invalid credentials")
            uid = udata["id"]

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
@app.post("/api/jobs/search")
async def search_jobs(search: JobSearch, current_user: dict = Depends(get_current_user)):
    """Search jobs from multiple sources."""
    try:
        print(f"[JOBS] Searching: {search.keyword} in {search.location}")
        
        jobs = [
            {
                "title": "Senior Python Developer",
                "company": "Google",
                "location": "Bangalore",
                "salary": "20-30 LPA",
                "description": "Looking for a senior Python developer with AWS experience...",
                "skills": ["python", "aws", "docker"],
                "source": "Indeed",
                "sourceUrl": "https://indeed.com/jobs?q=python",
                "postedDate": "2026-06-28"
            },
            {
                "title": "Full Stack Developer",
                "company": "Microsoft",
                "location": "Hyderabad",
                "salary": "18-25 LPA",
                "description": "Full stack developer with React and Node.js experience...",
                "skills": ["react", "node.js", "sql"],
                "source": "Naukri",
                "sourceUrl": "https://naukri.com/jobs",
                "postedDate": "2026-06-27"
            },
            {
                "title": "Backend Engineer",
                "company": "Amazon",
                "location": "Bangalore",
                "salary": "22-32 LPA",
                "description": "Backend engineer with Java and microservices experience...",
                "skills": ["java", "spring boot", "kubernetes"],
                "source": "Internshala",
                "sourceUrl": "https://internshala.com/jobs",
                "postedDate": "2026-06-26"
            }
        ]
        
        return {"total": len(jobs), "jobs": jobs}
    except Exception as e:
        print(f"[JOBS] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
async def get_jobs(current_user: dict = Depends(get_current_user)):
    """Get all jobs."""
    try:
        print(f"[JOBS] Getting all jobs")
        jobs = FirestoreService.search_jobs()
        return {"jobs": jobs if jobs else []}
    except Exception as e:
        print(f"[JOBS] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific job."""
    try:
        print(f"[JOBS] Getting job {job_id}")
        # Return demo job
        return {
            "title": "Senior Developer",
            "company": "Tech Company",
            "location": "Bangalore"
        }
    except Exception as e:
        print(f"[JOBS] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= APPLICATION ROUTES =============
@app.post("/api/applications")
async def apply_job(app: JobApplication, current_user: dict = Depends(get_current_user)):
    """Create job application."""
    try:
        uid = current_user['user_id']
        aid = str(uuid.uuid4())
        print(f"[APP] Creating application {aid}")
        
        ok = FirestoreService.save_job_application(uid, aid, app.dict())
        if ok:
            return {"message": "Application saved", "application_id": aid}
        raise HTTPException(status_code=500, detail="Save failed")
    except Exception as e:
        print(f"[APP] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/applications")
async def get_applications(current_user: dict = Depends(get_current_user)):
    """Get user applications."""
    try:
        uid = current_user['user_id']
        print(f"[APP] Getting applications for {uid}")
        apps = FirestoreService.get_user_applications(uid)
        return {"applications": apps if apps else []}
    except Exception as e:
        print(f"[APP] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/applications/{app_id}")
async def update_application(app_id: str, status: str, current_user: dict = Depends(get_current_user)):
    """Update application status."""
    try:
        uid = current_user['user_id']
        print(f"[APP] Updating {app_id} to {status}")
        ok = FirestoreService.update_application_status(uid, app_id, status)
        if ok:
            return {"message": "Updated"}
        raise HTTPException(status_code=500, detail="Update failed")
    except Exception as e:
        print(f"[APP] ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    try:
        return await run_in_threadpool(matcher.match, req.resume_text, req.job_description)
    except Exception as e:
        print(f"[MATCH] ERROR: {e}")
        raise HTTPException(status_code=500, detail="Matching failed")

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