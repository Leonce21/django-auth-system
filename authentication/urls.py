"""
Authentication URL patterns.
"""

from django.urls import path
from .views import (
    RegisterView, VerifyEmailView, ResendOTPView, LoginView,
    PasswordResetRequestView, PasswordResetConfirmView,
    PasswordUpdateView, UserProfileView, LogoutView
)

urlpatterns = [
    # Registration and verification
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Password management
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password/update/', PasswordUpdateView.as_view(), name='password-update'),
    
    # Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
]