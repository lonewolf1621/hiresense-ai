import os
from google.oauth2 import service_account
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage

# Path to your downloaded service account JSON
SERVICE_ACCOUNT_PATH = "service-account-key.json"

def init_firebase():
    """Initialize Firebase with service account"""
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'hiresense-ai-resumes.appspot.com'
        })
    
    return {
        'auth': auth,
        'db': firestore.client(),
        'storage': storage.bucket()
    }

# Get Firebase instances
firebase = init_firebase()
db = firebase['db']
storage_bucket = firebase['storage']