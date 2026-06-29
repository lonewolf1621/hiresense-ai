from config.firebase_config import storage_bucket
import os

class CloudStorageService:
    """Handle Cloud Storage operations"""

    @staticmethod
    def upload_resume(user_id: str, file_path: str, file_name: str):
        """Upload resume to Cloud Storage"""
        try:
            # Create path: resumes/{user_id}/{file_name}
            blob_path = f"resumes/{user_id}/{file_name}"
            blob = storage_bucket.blob(blob_path)
            
            # Upload file
            blob.upload_from_filename(file_path)
            
            # Make it publicly accessible (optional)
            blob.make_public()
            
            # Return public URL
            return blob.public_url
        except Exception as e:
            print(f"Error uploading resume: {e}")
            return None

    @staticmethod
    def upload_resume_bytes(user_id: str, file_bytes: bytes, file_name: str):
        """Upload resume from bytes"""
        try:
            blob_path = f"resumes/{user_id}/{file_name}"
            blob = storage_bucket.blob(blob_path)
            blob.upload_from_string(file_bytes)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            print(f"Error uploading resume: {e}")
            return None

    @staticmethod
    def download_resume(user_id: str, file_name: str):
        """Download resume from Cloud Storage"""
        try:
            blob_path = f"resumes/{user_id}/{file_name}"
            blob = storage_bucket.blob(blob_path)
            return blob.download_as_bytes()
        except Exception as e:
            print(f"Error downloading resume: {e}")
            return None

    @staticmethod
    def delete_resume(user_id: str, file_name: str):
        """Delete resume from Cloud Storage"""
        try:
            blob_path = f"resumes/{user_id}/{file_name}"
            blob = storage_bucket.blob(blob_path)
            blob.delete()
            return True
        except Exception as e:
            print(f"Error deleting resume: {e}")
            return False

    @staticmethod
    def list_user_resumes(user_id: str):
        """List all user's resumes"""
        try:
            prefix = f"resumes/{user_id}/"
            blobs = storage_bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            print(f"Error listing resumes: {e}")
            return []