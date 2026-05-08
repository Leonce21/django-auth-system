"""
Serializers for authentication endpoints.
Handles data validation, transformation, and error messages.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import logging

User = get_user_model()
logger = logging.getLogger('authentication')

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Validates:
        - Password strength (min 8 chars, complexity)
        - Email uniqueness and format
        - Required fields presence
        - Profile image format
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters with letters and numbers"
    )
    
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Must match the password field"
    )
    
    # Accept base64 image or file upload
    profile_image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Profile image (JPEG, PNG, max 5MB)"
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password_confirm', 'profile_image')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value: str) -> str:
        """Validate email format and uniqueness."""
        try:
            validate_email(value)
        except ValidationError:
            logger.warning(f"Invalid email format attempted: {value}")
            raise serializers.ValidationError("Enter a valid email address.")
        
        # Check if email already exists
        if User.objects.filter(email=value.lower().strip()).exists():
            logger.warning(f"Duplicate registration attempt for email: {value}")
            raise serializers.ValidationError("A user with this email already exists.")
        
        return value.lower().strip()
    
    def validate(self, attrs: dict) -> dict:
        """Validate password confirmation match."""
        if attrs['password'] != attrs['password_confirm']:
            logger.debug("Password confirmation mismatch during registration")
            raise serializers.ValidationError({"password_confirm": "Password fields didn't match."})
        return attrs
    
    def validate_profile_image(self, value):
        """Validate image file size and format."""
        if value:
            # Max 5MB
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image size must not exceed 5MB.")
            
            # Validate format
            if not value.content_type in ['image/jpeg', 'image/png', 'image/jpg']:
                raise serializers.ValidationError("Only JPEG and PNG images are allowed.")
        return value
    
    def create(self, validated_data: dict) -> User:
        """
        Create new user with hashed password and trigger OTP generation.
        
        Args:
            validated_data: Cleaned and validated registration data
            
        Returns:
            User: Newly created user instance
        """
        # Remove password_confirm from data
        validated_data.pop('password_confirm')
        profile_image = validated_data.pop('profile_image', None)
        
        # Extract password
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create(**validated_data)
        user.set_password(password)  # Hash password properly
        
        # Handle profile image upload to Supabase if provided
        if profile_image:
            from .services import SupabaseStorageService
            storage_service = SupabaseStorageService()
            image_url = storage_service.upload_profile_image(user.id, profile_image)
            user.profile_image = image_url
            logger.info(f"Profile image uploaded for user {user.email}")
        
        user.save()
        
        logger.info(f"New user registered: {user.email}")
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification via OTP.
    """
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        help_text="6-digit OTP code sent to email"
    )


class ResendOTPSerializer(serializers.Serializer):
    """
    Serializer for requesting OTP resend.
    """
    email = serializers.EmailField(required=True)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting password reset OTP.
    """
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset with OTP.
    """
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs: dict) -> dict:
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Passwords didn't match."})
        return attrs


class PasswordUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating password while logged in.
    """
    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs: dict) -> dict:
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Passwords didn't match."})
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data retrieval.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'profile_image', 
                  'is_email_verified', 'email_verified_at', 'created_at', 'updated_at')
        read_only_fields = ('id', 'email', 'is_email_verified', 'email_verified_at', 
                           'created_at', 'updated_at')
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        logger.info(f"[PROFILE_SERIALIZER] Returning profile for {instance.email}, profile_image: {data.get('profile_image')}")
        return data