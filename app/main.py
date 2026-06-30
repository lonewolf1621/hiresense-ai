from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
import uvicorn
import os
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import uuid

from config.firebase_config import db, storage_bucket
from app.services.firestore_service import FirestoreService
from app.services.cloud_storage_service import CloudStorageService
from scrapers.indeed_scraper import IndeedScraper
from scrapers.naukri_scraper import NaukriScraper
from scrapers.internshala_scraper import InternshalaScraper

# ============= CONFIG =============
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI App
app = FastAPI(title="HireSense API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= MODELS =============
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = ""

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

class ResumeUpload(BaseModel):
    name: str
    isPrimary: bool = False

class JobApplication(BaseModel):
    jobId: str
    jobTitle: str
    company: str
    matchScore: float
    notes: Optional[str] = ""

class JobSearch(BaseModel):
    keyword: str
    location: str = "India"
    source: Optional[str] = None  # Indeed, Naukri, Internshala

# ============= UTILITY FUNCTIONS =============
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============= DEPENDENCY =============
async def get_current_user(authorization: Optional[str] = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = authorization.split(" ")[1]  # Bearer <token>
        return verify_token(token)
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")

# ============= AUTH ROUTES =============
@app.post("/api/auth/register")
async def register(user: UserRegister):
    """Register a new user"""
    try:
        # Check if user exists
        user_ref = db.collection('users').where('email', '==', user.email).stream()
        if list(user_ref):
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create new user document
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(user.password)
        
        db.collection('users').document(user_id).set({
            'email': user.email,
            'name': user.name,
            'phone': user.phone,
            'password': hashed_password,
            'profile': {
                'experience': 0,
                'skills': [],
                'targetRoles': [],
                'targetCities': [],
                'targetCompanies': [],
                'createdAt': datetime.now()
            },
            'resumes': {},
            'applications': {}
        })
        
        # Create access token
        access_token = create_access_token(data={"sub": user_id})
        
        return {
            "message": "User registered successfully",
            "user_id": user_id,
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/auth/login")
async def login(user: UserLogin):
    """Login user"""
    try:
        # Find user by email
        user_ref = db.collection('users').where('email', '==', user.email).stream()
        user_docs = list(user_ref)
        
        if not user_docs:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user_doc = user_docs[0]
        user_data = user_doc.to_dict()
        user_id = user_doc.id
        
        # Verify password
        if not verify_password(user.password, user_data.get('password', '')):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create access token
        access_token = create_access_token(data={"sub": user_id})
        
        return {
            "message": "Login successful",
            "user_id": user_id,
            "name": user_data.get('name'),
            "email": user_data.get('email'),
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

# ============= PROFILE ROUTES =============
@app.get("/api/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile"""
    try:
        user_id = current_user['user_id']
        user_data = FirestoreService.get_user_profile(user_id)
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/profile")
async def update_profile(profile: UserProfile, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    try:
        user_id = current_user['user_id']
        success = FirestoreService.update_user_profile(user_id, profile.dict())
        
        if success:
            return {"message": "Profile updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update profile")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= RESUME ROUTES =============
@app.post("/api/resumes/upload")
async def upload_resume(
    file: UploadFile = File(...),
    name: str = Form(...),
    isPrimary: bool = Form(False),
    current_user: dict = Depends(get_current_user)
):
    """Upload resume file"""
    try:
        user_id = current_user['user_id']
        
        # Read file
        contents = await file.read()
        
        # Upload to Cloud Storage
        gcs_url = CloudStorageService.upload_resume_bytes(user_id, contents, file.filename)
        
        if not gcs_url:
            raise HTTPException(status_code=500, detail="Failed to upload resume")
        
        # Save metadata to Firestore
        resume_id = str(uuid.uuid4())
        success = FirestoreService.save_resume(user_id, resume_id, {
            'name': name,
            'gcsUrl': gcs_url,
            'isPrimary': isPrimary
        })
        
        if success:
            return {
                "message": "Resume uploaded successfully",
                "resume_id": resume_id,
                "url": gcs_url
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save resume metadata")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumes")
async def get_resumes(current_user: dict = Depends(get_current_user)):
    """Get user resumes"""
    try:
        user_id = current_user['user_id']
        resumes = FirestoreService.get_user_resumes(user_id)
        return {"resumes": resumes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/resumes/{resume_id}")
async def delete_resume(resume_id: str, current_user: dict = Depends(get_current_user)):
    """Delete resume"""
    try:
        user_id = current_user['user_id']
        # Delete from Cloud Storage
        success = CloudStorageService.delete_resume(user_id, resume_id)
        
        if success:
            return {"message": "Resume deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete resume")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= JOB ROUTES =============
@app.post("/api/jobs/search")
async def search_jobs(search: JobSearch, current_user: dict = Depends(get_current_user)):
    """Search jobs from multiple sources"""
    try:
        jobs = []
        
        # Indeed
        if not search.source or search.source == "Indeed":
            indeed_jobs = IndeedScraper.scrape_jobs(search.keyword, search.location, pages=1)
            jobs.extend(indeed_jobs)
        
        # Naukri
        if not search.source or search.source == "Naukri":
            naukri_jobs = NaukriScraper.scrape_jobs(search.keyword, search.location, pages=1)
            jobs.extend(naukri_jobs)
        
        # Internshala
        if not search.source or search.source == "Internshala":
            internshala_jobs = InternshalaScraper.scrape_jobs(search.keyword, search.location, pages=1)
            jobs.extend(internshala_jobs)
        
        # Save to Firestore
        for job in jobs:
            job_id = str(uuid.uuid4())
            FirestoreService.save_job(job_id, job)
        
        return {
            "total": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
async def get_jobs(current_user: dict = Depends(get_current_user)):
    """Get all jobs"""
    try:
        jobs = FirestoreService.search_jobs()
        return {"jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= APPLICATION ROUTES =============
@app.post("/api/applications")
async def apply_job(app: JobApplication, current_user: dict = Depends(get_current_user)):
    """Apply for a job"""
    try:
        user_id = current_user['user_id']
        app_id = str(uuid.uuid4())
        
        success = FirestoreService.save_job_application(user_id, app_id, app.dict())
        
        if success:
            return {
                "message": "Application saved successfully",
                "application_id": app_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save application")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/applications")
async def get_applications(current_user: dict = Depends(get_current_user)):
    """Get user applications"""
    try:
        user_id = current_user['user_id']
        applications = FirestoreService.get_user_applications(user_id)
        return {"applications": applications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/applications/{app_id}")
async def update_application(app_id: str, status: str, current_user: dict = Depends(get_current_user)):
    """Update application status"""
    try:
        user_id = current_user['user_id']
        success = FirestoreService.update_application_status(user_id, app_id, status)
        
        if success:
            return {"message": "Application updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update application")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= HEALTH CHECK =============
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ============= ROOT =============
@app.get("/")
async def root():
    return {
        "message": "HireSense API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)