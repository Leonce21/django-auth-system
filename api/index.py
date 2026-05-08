"""
Vercel Serverless Entry Point for Django
"""

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mark as Vercel environment
os.environ.setdefault('VERCEL', 'true')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Import Django WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Vercel expects 'app' variable
app = application