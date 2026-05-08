"""
Supabase client initialization and configuration.
Provides database and storage access.
"""

from supabase import create_client, Client
from django.conf import settings
import logging

logger = logging.getLogger('authentication')

# Global client instance (singleton pattern)
_supabase_client: Client = None

def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance.
    
    Returns:
        Client: Configured Supabase client
    """
    global _supabase_client
    
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY  # Use service key for admin operations
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    return _supabase_client


def get_supabase_db():
    """
    Get Supabase database reference for raw SQL operations if needed.
    
    Returns:
        PostgREST client for database operations
    """
    client = get_supabase_client()
    return client.table('auth_users')  # Reference to our custom table