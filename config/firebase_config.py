import os
import json
from pathlib import Path

try:
    import firebase_admin
    from firebase_admin import credentials, auth, firestore, storage
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# Path to service account key
SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "service-account-key.json")

def init_firebase():
    """Initialize Firebase with service account"""
    if not FIREBASE_AVAILABLE:
        print("❌ Firebase Admin SDK not available")
        return {
            'auth': None,
            'db': None,
            'storage': None
        }
    
    # Check if service account file exists
    if not Path(SERVICE_ACCOUNT_PATH).exists():
        print(f"⚠️ {SERVICE_ACCOUNT_PATH} not found")
        print("Using in-memory fallback mode")
        return {
            'auth': None,
            'db': None,
            'storage': None
        }
    
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv('GCS_BUCKET_NAME', 'hiresense-ai-resumes.appspot.com')
            })
            print("✅ Firebase initialized successfully with GCP credentials")
        
        return {
            'auth': auth,
            'db': firestore.client(),
            'storage': storage.bucket()
        }
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        print("Using in-memory fallback mode")
        return {
            'auth': None,
            'db': None,
            'storage': None
        }

# Initialize Firebase
firebase = init_firebase()
db = firebase['db']
storage_bucket = firebase['storage']