"""
Custom User model with email verification, OTP, and Supabase storage integration.
Extends AbstractUser to add OTP fields and email verification status.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import logging

# Initialize logger for this module
logger = logging.getLogger('authentication')

class User(AbstractUser):
    """
    Custom User model with email verification and OTP capabilities.
    
    Fields:
        email: Unique email address (used for login)
        is_email_verified: Boolean tracking email verification status
        email_verified_at: Timestamp when email was verified
        otp_code: Current OTP code for verification/reset
        otp_expires_at: When the current OTP expires
        otp_attempts: Number of failed OTP attempts
        profile_image: URL to image stored in Supabase Storage
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    # Override username to use email as primary identifier
    username = models.CharField(max_length=150, unique=False, blank=True, null=True)
    email = models.EmailField(unique=True, db_index=True)
    
    # Email verification fields
    is_email_verified = models.BooleanField(default=False, db_index=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    # OTP fields for verification and password reset
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveSmallIntegerField(default=0)
    
    # Profile image stored in Supabase (URL reference)
    profile_image = models.URLField(
        max_length=500, 
        null=True, 
        blank=True,
        help_text="URL to profile image in Supabase Storage"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Specify email as the username field for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_users'
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email', 'is_email_verified']),
            models.Index(fields=['otp_code', 'otp_expires_at']),
        ]
    
    def __str__(self):
        return f"{self.email} ({'Verified' if self.is_email_verified else 'Unverified'})"
    
    def is_otp_valid(self, code: str) -> bool:
        """
        Validate if provided OTP code is correct and not expired.
        
        Args:
            code: The OTP code to validate
            
        Returns:
            bool: True if OTP is valid and not expired, False otherwise
        """
        logger.debug(f"Validating OTP for user {self.email}")
        
        # Check if OTP exists
        if not self.otp_code or not self.otp_expires_at:
            logger.warning(f"No OTP found for user {self.email}")
            return False
        
        # Check if OTP is expired
        if timezone.now() > self.otp_expires_at:
            logger.info(f"OTP expired for user {self.email}")
            return False
        
        # Check if max attempts exceeded
        if self.otp_attempts >= 3:
            logger.warning(f"Max OTP attempts exceeded for user {self.email}")
            return False
        
        # Validate code
        is_valid = self.otp_code == code
        if not is_valid:
            self.otp_attempts += 1
            self.save(update_fields=['otp_attempts'])
            logger.warning(f"Invalid OTP attempt {self.otp_attempts}/3 for user {self.email}")
        else:
            logger.info(f"OTP validated successfully for user {self.email}")
        
        return is_valid
    
    def generate_otp(self) -> str:
        """
        Generate a new 6-digit OTP and set expiration.
        
        Returns:
            str: The generated 6-digit OTP code
        """
        import random
        code = f"{random.randint(100000, 999999)}"
        
        self.otp_code = code
        # OTP expires in 10 minutes (configurable via settings)
        from django.conf import settings
        self.otp_expires_at = timezone.now() + timedelta(minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10))
        self.otp_attempts = 0  # Reset attempts
        
        self.save(update_fields=['otp_code', 'otp_expires_at', 'otp_attempts'])
        
        logger.info(f"Generated new OTP for user {self.email}, expires at {self.otp_expires_at}")
        return code
    
    def clear_otp(self):
        """Clear OTP fields after successful verification."""
        self.otp_code = None
        self.otp_expires_at = None
        self.otp_attempts = 0
        self.save(update_fields=['otp_code', 'otp_expires_at', 'otp_attempts'])
        logger.debug(f"Cleared OTP for user {self.email}")
    
    def mark_email_verified(self):
        """Mark user's email as verified."""
        self.is_email_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=['is_email_verified', 'email_verified_at'])
        logger.info(f"Email verified for user {self.email}")