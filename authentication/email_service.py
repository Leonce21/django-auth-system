"""
Email service for sending OTP and verification emails.
Uses Django's SMTP backend with Gmail (free) - similar to Nodemailer in Node.js.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger('authentication')

class EmailService:
    """
    Service for sending transactional emails.
    Uses Gmail SMTP (free tier) via Django's email backend.
    """
    
    @staticmethod
    def send_otp_email(email: str, otp_code: str, purpose: str = "verification") -> bool:
        """
        Send OTP code via email using Gmail SMTP.
        
        Args:
            email: Recipient email address
            otp_code: 6-digit OTP code
            purpose: Either 'verification' or 'password_reset'
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Determine email template based on purpose
            if purpose == "password_reset":
                subject = "Password Reset Request - DigiAuth"
                template_name = "emails/password_reset_otp.html"
                action_text = "reset your password"
            else:
                subject = "Email Verification - DigiAuth"
                template_name = "emails/verification_otp.html"
                action_text = "verify your email"
            
            # Context for email template
            context = {
                'otp_code': otp_code,
                'expiry_minutes': getattr(settings, 'OTP_EXPIRY_MINUTES', 10),
                'action_text': action_text,
                'site_name': 'DigiAuth',
            }
            
            # Render HTML and plain text versions
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            
            # Send email using Django's send_mail (uses Gmail SMTP backend)
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"OTP email sent successfully to {email} for {purpose}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(email: str, first_name: str) -> bool:
        """Send welcome email after successful verification."""
        try:
            subject = "Welcome to DigiAuth!"
            context = {'first_name': first_name, 'site_name': 'DigiAuth'}
            
            html_message = render_to_string("emails/welcome.html", context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Welcome email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {str(e)}")
            return False