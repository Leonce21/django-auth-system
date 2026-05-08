"""
Business logic services for authentication.
Handles Supabase storage operations and complex workflows.
"""

import uuid
from typing import Optional
from django.conf import settings
from supabase import Client
from .supabase_client import get_supabase_client
import logging

logger = logging.getLogger('authentication')

class SupabaseStorageService:
    """
    Service for handling file uploads to Supabase Storage.
    Manages profile images and other user assets.
    """
    
    BUCKET_NAME = 'profile-images'
    
    def __init__(self):
        self.client: Client = get_supabase_client()
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the storage bucket exists, create if not."""
        try:
            buckets = self.client.storage.list_buckets()
            bucket_names = [b['name'] for b in buckets]
            
            if self.BUCKET_NAME not in bucket_names:
                self.client.storage.create_bucket(
                    self.BUCKET_NAME,
                    options={'public': True}
                )
                logger.info(f"Created Supabase storage bucket: {self.BUCKET_NAME}")
        except Exception as e:
            logger.warning(f"Bucket check/creation warning: {str(e)}")
    
    def upload_profile_image(self, user_id: int, image_file) -> str:
        """
        Upload profile image to Supabase Storage.
        Returns a SIGNED URL that works for 1 week (604800 seconds).
        """
        try:
            file_extension = image_file.name.split('.')[-1].lower()
            unique_filename = f"{user_id}/{uuid.uuid4()}.{file_extension}"
            
            file_content = image_file.read()
            
            # Upload to Supabase Storage
            result = self.client.storage.from_(self.BUCKET_NAME).upload(
                path=unique_filename,
                file=file_content,
                file_options={'content-type': image_file.content_type}
            )
            
            # Create SIGNED URL (valid for 7 days = 604800 seconds)
            # Signed URLs work even if bucket is not public
            signed_url_response = self.client.storage.from_(self.BUCKET_NAME).create_signed_url(
                path=unique_filename,
                expires_in=604800  # 7 days
            )
            
            # Handle different response formats from supabase-py
            if isinstance(signed_url_response, dict):
                signed_url = signed_url_response.get('signedURL') or signed_url_response.get('signedUrl', '')
            else:
                signed_url = str(signed_url_response)
            
            logger.info(f"Profile image uploaded for user {user_id}: {signed_url[:60]}...")
            return signed_url
            
        except Exception as e:
            logger.error(f"Failed to upload profile image: {str(e)}")
            raise
    
    def delete_profile_image(self, image_url: str) -> bool:
        """
        Delete profile image from Supabase Storage.
        Extracts path from signed URL.
        """
        try:
            # For signed URLs, extract path between bucket name and ?token=
            import re
            # Pattern: .../profile-images/<path>?token=...
            match = re.search(r'profile-images/([^?]+)', image_url)
            if match:
                path = match.group(1)
                self.client.storage.from_(self.BUCKET_NAME).remove([path])
                logger.info(f"Deleted profile image: {path}")
                return True
            else:
                logger.warning(f"Could not extract path from URL: {image_url[:60]}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete profile image: {str(e)}")
            return False