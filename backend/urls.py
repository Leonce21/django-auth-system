"""
Root URL configuration.
Includes authentication URLs and Swagger documentation.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configure Swagger/OpenAPI documentation
schema_view = get_schema_view(
    openapi.Info(
        title="DigiAuth API",
        default_version='v1',
        description="""
        Professional Authentication API with JWT, OTP verification, and Supabase storage.
        
        Features:
        - User registration with email verification
        - JWT login with refresh tokens
        - OTP-based password reset
        - Profile image upload to Supabase Storage
        - Secure password management
        """,
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Authentication API endpoints
    path('api/auth/', include('authentication.urls')),
    
    # Swagger documentation URLs
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)