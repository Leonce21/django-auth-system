"""
Authentication API views.
Handles registration, login, OTP verification, password reset, and profile management.
"""

from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .serializers import (
    UserRegistrationSerializer, EmailVerificationSerializer, ResendOTPSerializer,
    LoginSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    PasswordUpdateSerializer, UserProfileSerializer
)
from .email_service import EmailService

User = get_user_model()
logger = logging.getLogger('authentication')


class RegisterView(APIView):
    """
    POST /api/auth/register/
    
    Register a new user with email, password, and optional profile image.
    Sends OTP to email for verification.
    """
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        security=[],
        request_body=UserRegistrationSerializer,
        operation_description="Register new user with email verification",
        responses={
            201: openapi.Response('User registered, OTP sent', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )),
            400: 'Validation error'
        }
    )
    def post(self, request):
        logger.info(f"Registration attempt from IP: {request.META.get('REMOTE_ADDR')}")
        
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Create user (inactive until email verified)
                    user = serializer.save()
                    user.is_active = False  # Deactivate until verified
                    user.save()
                    
                    # Generate OTP and send email
                    otp_code = user.generate_otp()
                    email_sent = EmailService.send_otp_email(
                        email=user.email,
                        otp_code=otp_code,
                        purpose="verification"
                    )
                    
                    if not email_sent:
                        # If email fails, still return success but warn user
                        logger.error(f"Failed to send verification email to {user.email}")
                        return Response({
                            'message': 'Account created but email service unavailable. Please request OTP resend.',
                            'email': user.email,
                            'warning': 'Email delivery failed'
                        }, status=status.HTTP_201_CREATED)
                    
                    logger.info(f"User {user.email} registered successfully, awaiting verification")
                    
                    return Response({
                        'message': 'Registration successful. Please check your email for verification OTP.',
                        'email': user.email,
                        'expires_in': '10 minutes'
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                logger.error(f"Registration failed: {str(e)}")
                return Response({
                    'error': 'Registration failed. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.warning(f"Registration validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """
    POST /api/auth/verify-email/
    
    Verify email using OTP code sent during registration.
    """
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        request_body=EmailVerificationSerializer,
        operation_description="Verify email with OTP code",
        responses={200: 'Email verified', 400: 'Invalid or expired OTP'}
    )
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            
            try:
                user = User.objects.get(email=email.lower().strip())
            except User.DoesNotExist:
                logger.warning(f"Verification attempt for non-existent email: {email}")
                return Response({
                    'error': 'User not found.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate OTP
            if user.is_otp_valid(otp_code):
                # Mark email as verified and activate account
                user.mark_email_verified()
                user.is_active = True
                user.save()
                user.clear_otp()
                
                # Send welcome email
                EmailService.send_welcome_email(user.email, user.first_name)
                
                # Generate tokens for immediate login
                refresh = RefreshToken.for_user(user)
                
                logger.info(f"Email verified for user: {email}")
                
                return Response({
                    'message': 'Email verified successfully. Welcome!',
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    }
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Invalid/expired OTP attempt for {email}")
                return Response({
                    'error': 'Invalid or expired OTP code. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    """
    POST /api/auth/resend-otp/
    
    Resend OTP code for email verification or password reset.
    """
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        security=[],
        request_body=ResendOTPSerializer,
        operation_description="Request new OTP code",
        responses={200: 'OTP resent', 429: 'Too many requests'}
    )
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email.lower().strip())
            except User.DoesNotExist:
                # Return generic message to prevent email enumeration
                logger.info(f"OTP resend attempt for non-existent email: {email}")
                return Response({
                    'message': 'If an account exists, a new OTP has been sent.'
                }, status=status.HTTP_200_OK)
            
            # Generate new OTP
            otp_code = user.generate_otp()
            
            # Determine purpose based on user state
            purpose = "password_reset" if user.is_email_verified else "verification"
            
            # Send email
            email_sent = EmailService.send_otp_email(email, otp_code, purpose)
            
            if email_sent:
                logger.info(f"OTP resent to {email} for {purpose}")
                return Response({
                    'message': 'New OTP sent. Please check your email.',
                    'expires_in': '10 minutes'
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Failed to resend OTP to {email}")
                return Response({
                    'error': 'Failed to send email. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/auth/login/
    
    Authenticate user with email and password, return JWT tokens.
    """
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        security=[],
        request_body=LoginSerializer,
        operation_description="Login with email and password",
        responses={
            200: openapi.Response('Login successful', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'tokens': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )),
            401: 'Invalid credentials'
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            # Authenticate user
            user = authenticate(request, username=email, password=password)
            
            if user is None:
                logger.warning(f"Failed login attempt for {email}")
                return Response({
                    'error': 'Invalid email or password.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if email is verified
            if not user.is_email_verified:
                logger.warning(f"Login attempt for unverified email: {email}")
                return Response({
                    'error': 'Please verify your email before logging in.',
                    'requires_verification': True,
                    'email': email
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login attempt for inactive account: {email}")
                return Response({
                    'error': 'Account is deactivated. Please contact support.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            logger.info(f"Successful login for user: {email}")
            
            return Response({
                'message': 'Login successful.',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile_image': user.profile_image,
                    'is_email_verified': user.is_email_verified,
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/request/
    
    Request password reset OTP.
    """
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer,
        operation_description="Request password reset OTP",
        responses={200: 'OTP sent if email exists'}
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email.lower().strip(), is_email_verified=True)
                
                # Generate OTP for password reset
                otp_code = user.generate_otp()
                email_sent = EmailService.send_otp_email(email, otp_code, "password_reset")
                
                if email_sent:
                    logger.info(f"Password reset OTP sent to {email}")
                    return Response({
                        'message': 'If an account exists, a password reset OTP has been sent.',
                        'expires_in': '10 minutes'
                    }, status=status.HTTP_200_OK)
                else:
                    logger.error(f"Failed to send password reset email to {email}")
                    return Response({
                        'error': 'Failed to send email. Please try again.'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except User.DoesNotExist:
                # Generic response to prevent email enumeration
                logger.info(f"Password reset attempt for non-existent/unverified email: {email}")
                return Response({
                    'message': 'If an account exists, a password reset OTP has been sent.'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password-reset/confirm/
    
    Confirm password reset with OTP and set new password.
    """
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer,
        operation_description="Reset password using OTP",
        responses={200: 'Password reset successful'}
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            new_password = serializer.validated_data['new_password']
            
            try:
                user = User.objects.get(email=email.lower().strip())
            except User.DoesNotExist:
                logger.warning(f"Password reset confirm for non-existent email: {email}")
                return Response({
                    'error': 'Invalid request.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate OTP
            if not user.is_otp_valid(otp_code):
                return Response({
                    'error': 'Invalid or expired OTP code.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(new_password)
            user.clear_otp()  # Clear OTP after successful use
            user.save()
            
            # Blacklist all existing tokens for security
            try:
                # Note: This requires token blacklist app
                for token in user.outstandingtoken_set.all():
                    token.blacklist()
            except:
                pass
            
            logger.info(f"Password reset successful for user: {email}")
            
            return Response({
                'message': 'Password reset successful. Please login with your new password.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordUpdateView(APIView):
    """
    PUT /api/auth/password/update/
    
    Update password while logged in (requires current password).
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=PasswordUpdateSerializer,
        operation_description="Update password (requires authentication)",
        responses={200: 'Password updated', 400: 'Invalid current password'}
    )
    def put(self, request):
        serializer = PasswordUpdateSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']
            
            # Verify current password
            if not user.check_password(current_password):
                logger.warning(f"Failed password update for user {user.email} - wrong current password")
                return Response({
                    'error': 'Current password is incorrect.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Generate new tokens (optional - forces re-login)
            refresh = RefreshToken.for_user(user)
            
            logger.info(f"Password updated successfully for user: {user.email}")
            
            return Response({
                'message': 'Password updated successfully.',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    GET /api/auth/profile/
    PUT /api/auth/profile/
    
    Retrieve or update user profile.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get current user profile",
        responses={200: UserProfileSerializer}
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        logger.debug(f"Profile retrieved for user: {request.user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        request_body=UserProfileSerializer,
        operation_description="Update user profile",
        responses={200: UserProfileSerializer}
    )
    def put(self, request):
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Profile updated for user: {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    
    Blacklist refresh token to force logout.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to blacklist')
            },
            required=['refresh']
        ),
        operation_description="Logout and blacklist refresh token",
        responses={200: 'Logout successful'}
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'error': 'Refresh token is required.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"User {request.user.email} logged out successfully")
            return Response({
                'message': 'Logout successful.'
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            logger.warning("Logout attempt with invalid token")
            return Response({
                'error': 'Invalid or expired token.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({
                'error': 'Logout failed.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/
    
    Refresh access token using valid refresh token.
    """
    
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        security=[],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['refresh']
        ),
        operation_description="Refresh access token",
        responses={200: 'New tokens generated'}
    )
    def post(self, request):
        from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
        # Delegate to built-in view
        return BaseTokenRefreshView.as_view()(request._request)