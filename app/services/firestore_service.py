from config.firebase_config import db
from datetime import datetime
from typing import Dict, List, Optional

class FirestoreService:
    """Handle all Firestore database operations"""

    @staticmethod
    def create_user_profile(user_id: str, profile_data: Dict):
        """Create user profile in Firestore"""
        try:
            db.collection('users').document(user_id).set({
                'profile': {
                    'email': profile_data.get('email'),
                    'name': profile_data.get('name'),
                    'phone': profile_data.get('phone', ''),
                    'experience': profile_data.get('experience', 0),
                    'skills': profile_data.get('skills', []),
                    'targetRoles': profile_data.get('targetRoles', []),
                    'targetCities': profile_data.get('targetCities', []),
                    'targetCompanies': profile_data.get('targetCompanies', []),
                    'profilePicture': '',
                    'createdAt': datetime.now(),
                    'updatedAt': datetime.now()
                },
                'resumes': {},
                'savedJobs': {},
                'applications': {},
                'analysisHistory': {}
            })
            return True
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return False

    @staticmethod
    def get_user_profile(user_id: str):
        """Get user profile"""
        try:
            doc = db.collection('users').document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None

    @staticmethod
    def update_user_profile(user_id: str, updates: Dict):
        """Update user profile"""
        try:
            db.collection('users').document(user_id).update({
                'profile': updates,
                'profile.updatedAt': datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False

    @staticmethod
    def save_resume(user_id: str, resume_id: str, resume_data: Dict):
        """Save resume metadata"""
        try:
            db.collection('users').document(user_id).collection('resumes').document(resume_id).set({
                'name': resume_data.get('name'),
                'gcsUrl': resume_data.get('gcsUrl'),
                'uploadedDate': datetime.now(),
                'isPrimary': resume_data.get('isPrimary', False)
            })
            return True
        except Exception as e:
            print(f"Error saving resume: {e}")
            return False

    @staticmethod
    def get_user_resumes(user_id: str):
        """Get all user resumes"""
        try:
            resumes = db.collection('users').document(user_id).collection('resumes').stream()
            return [doc.to_dict() for doc in resumes]
        except Exception as e:
            print(f"Error getting resumes: {e}")
            return []

    @staticmethod
    def save_job_application(user_id: str, app_id: str, app_data: Dict):
        """Save job application"""
        try:
            db.collection('users').document(user_id).collection('applications').document(app_id).set({
                'jobId': app_data.get('jobId'),
                'jobTitle': app_data.get('jobTitle'),
                'company': app_data.get('company'),
                'status': app_data.get('status', 'Applied'),  # Applied, Rejected, Interview, Offer
                'appliedDate': datetime.now(),
                'matchScore': app_data.get('matchScore'),
                'notes': app_data.get('notes', '')
            })
            return True
        except Exception as e:
            print(f"Error saving application: {e}")
            return False

    @staticmethod
    def get_user_applications(user_id: str):
        """Get all user applications"""
        try:
            apps = db.collection('users').document(user_id).collection('applications').stream()
            return [doc.to_dict() for doc in apps]
        except Exception as e:
            print(f"Error getting applications: {e}")
            return []

    @staticmethod
    def update_application_status(user_id: str, app_id: str, status: str):
        """Update application status"""
        try:
            db.collection('users').document(user_id).collection('applications').document(app_id).update({
                'status': status,
                'updatedAt': datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error updating application: {e}")
            return False

    @staticmethod
    def save_job(job_id: str, job_data: Dict):
        """Save job to database"""
        try:
            db.collection('jobs').document(job_id).set({
                'title': job_data.get('title'),
                'company': job_data.get('company'),
                'location': job_data.get('location'),
                'salary': job_data.get('salary'),
                'description': job_data.get('description'),
                'skills': job_data.get('skills', []),
                'source': job_data.get('source'),  # Indeed, Naukri, Internshala
                'sourceUrl': job_data.get('sourceUrl'),
                'postedDate': job_data.get('postedDate'),
                'scrapedDate': datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error saving job: {e}")
            return False

    @staticmethod
    def search_jobs(filters: Dict = None):
        """Search jobs with filters"""
        try:
            query = db.collection('jobs')
            
            if filters:
                if filters.get('location'):
                    query = query.where('location', '==', filters['location'])
                if filters.get('minSalary'):
                    query = query.where('salary', '>=', filters['minSalary'])
                if filters.get('maxSalary'):
                    query = query.where('salary', '<=', filters['maxSalary'])
                if filters.get('source'):
                    query = query.where('source', '==', filters['source'])
            
            jobs = query.stream()
            return [doc.to_dict() for doc in jobs]
        except Exception as e:
            print(f"Error searching jobs: {e}")
            return []

    @staticmethod
    def save_analysis(user_id: str, analysis_id: str, analysis_data: Dict):
        """Save analysis history"""
        try:
            db.collection('users').document(user_id).collection('analysisHistory').document(analysis_id).set({
                'jobDescription': analysis_data.get('jobDescription'),
                'matchScore': analysis_data.get('matchScore'),
                'matchedSkills': analysis_data.get('matchedSkills'),
                'missingSkills': analysis_data.get('missingSkills'),
                'suggestions': analysis_data.get('suggestions'),
                'date': datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False