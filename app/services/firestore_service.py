from datetime import datetime
from typing import Dict, List, Optional

try:
    from config.firebase_config import db
    FIREBASE_AVAILABLE = db is not None
except:
    FIREBASE_AVAILABLE = False


class FirestoreService:
    """Handle all Firestore database operations"""

    @staticmethod
    def create_user_profile(user_id: str, profile_data: Dict):
        """Create user profile in Firestore"""
        if not FIREBASE_AVAILABLE:
            print(f"[DEMO] Created profile: {user_id}")
            return True
        
        try:
            db.collection('users').document(user_id).set({
                'email': profile_data.get('email'),
                'name': profile_data.get('name'),
                'phone': profile_data.get('phone', ''),
                'profile': {
                    'experience': profile_data.get('experience', 0),
                    'skills': profile_data.get('skills', []),
                    'targetRoles': profile_data.get('targetRoles', []),
                    'targetCities': profile_data.get('targetCities', []),
                    'targetCompanies': profile_data.get('targetCompanies', []),
                    'createdAt': datetime.now()
                }
            })
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    @staticmethod
    def get_user_profile(user_id: str):
        """Get user profile"""
        if not FIREBASE_AVAILABLE:
            return {
                'email': 'demo@example.com',
                'name': 'Demo User',
                'profile': {'skills': [], 'experience': 0}
            }
        
        try:
            doc = db.collection('users').document(user_id).get()
            return doc.to_dict() if doc.exists else None
        except:
            return None

    @staticmethod
    def update_user_profile(user_id: str, updates: Dict):
        """Update user profile"""
        if not FIREBASE_AVAILABLE:
            print(f"[DEMO] Updated profile: {user_id}")
            return True
        
        try:
            db.collection('users').document(user_id).update(updates)
            return True
        except:
            return False

    @staticmethod
    def save_resume(user_id: str, resume_id: str, resume_data: Dict):
        """Save resume metadata"""
        if not FIREBASE_AVAILABLE:
            print(f"[DEMO] Saved resume: {resume_id}")
            return True
        
        try:
            db.collection('users').document(user_id).collection('resumes').document(resume_id).set(resume_data)
            return True
        except:
            return False

    @staticmethod
    def get_user_resumes(user_id: str):
        """Get all user resumes"""
        if not FIREBASE_AVAILABLE:
            return []
        
        try:
            resumes = db.collection('users').document(user_id).collection('resumes').stream()
            return [doc.to_dict() for doc in resumes]
        except:
            return []

    @staticmethod
    def save_job_application(user_id: str, app_id: str, app_data: Dict):
        """Save job application"""
        if not FIREBASE_AVAILABLE:
            print(f"[DEMO] Saved application: {app_id}")
            return True
        
        try:
            db.collection('users').document(user_id).collection('applications').document(app_id).set(app_data)
            return True
        except:
            return False

    @staticmethod
    def get_user_applications(user_id: str):
        """Get all user applications"""
        if not FIREBASE_AVAILABLE:
            return []
        
        try:
            apps = db.collection('users').document(user_id).collection('applications').stream()
            return [doc.to_dict() for doc in apps]
        except:
            return []

    @staticmethod
    def update_application_status(user_id: str, app_id: str, status: str):
        """Update application status"""
        if not FIREBASE_AVAILABLE:
            return True
        
        try:
            db.collection('users').document(user_id).collection('applications').document(app_id).update({'status': status})
            return True
        except:
            return False

    @staticmethod
    def save_job(job_id: str, job_data: Dict):
        """Save job to database"""
        if not FIREBASE_AVAILABLE:
            print(f"[DEMO] Saved job: {job_id}")
            return True
        
        try:
            db.collection('jobs').document(job_id).set(job_data)
            return True
        except:
            return False

    @staticmethod
    def search_jobs(filters: Dict = None):
        """Search jobs with filters"""
        if not FIREBASE_AVAILABLE:
            return []
        
        try:
            query = db.collection('jobs')
            if filters:
                if filters.get('location'):
                    query = query.where('location', '==', filters['location'])
                if filters.get('source'):
                    query = query.where('source', '==', filters['source'])
            
            jobs = query.stream()
            return [doc.to_dict() for doc in jobs]
        except:
            return []

    @staticmethod
    def save_analysis(user_id: str, analysis_id: str, analysis_data: Dict):
        """Save analysis history"""
        if not FIREBASE_AVAILABLE:
            return True
        
        try:
            db.collection('users').document(user_id).collection('analysisHistory').document(analysis_id).set(analysis_data)
            return True
        except:
            return False