""""from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from account.models import OTP, User

@shared_task
def send_verification_code():
    print()
    print()
    print()
    print("This is good")
    print()
    print()
    print()
    return "Verification code sent successfully" """

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from account.models import OTP, User

@shared_task
def send_verification_code(user_id, otp_type=None):
    """
    Send verification code to user's email
    
    Args:
        user_id: User ID
        otp_type: Type of OTP (ACCOUNT_VERIFICATION, RESET_PASSWORD, etc.)
    """
    print("Starting send_verification_code task")
    try:
        user = User.objects.get(id=user_id)
        print(f"Found user: {user.email}")
        
        # Create OTP if not provided
        if otp_type is None:
            otp_type = OTP.ACCOUNT_VERIFICATION
            
        # Create new OTP
        otp = OTP.objects.create_otp(user=user, type=otp_type)
        print(f"Created OTP: {otp.otp}")
        
        # Get expiry time from settings
        expiry_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRY', 5)
        
        # Prepare email content based on OTP type
        if otp_type == OTP.ACCOUNT_VERIFICATION:
            subject = "Account Verification"
            message = f"Your verification code is: {otp.otp}\nThis code will expire in {expiry_minutes} minutes."
        elif otp_type == OTP.RESET_PASSWORD:
            subject = "Password Reset Request"
            message = f"Your password reset code is: {otp.otp}\nThis code will expire in {expiry_minutes} minutes."
        elif otp_type == OTP.CHANGE_EMAIL_REQUEST:
            subject = "Email Change Request"
            message = f"Your email change verification code is: {otp.otp}\nThis code will expire in {expiry_minutes} minutes."
        else:
            subject = "Verification Code"
            message = f"Your verification code is: {otp.otp}\nThis code will expire in {expiry_minutes} minutes."
        
        print(f"Sending email to: {user.email}")
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        print(f"Email sent successfully to {user.email}")
        return f"Verification code sent to {user.email}"
    except User.DoesNotExist:
        print(f"User with ID {user_id} not found")
        return "User not found"
    except Exception as e:
        print(f"Error sending verification code: {str(e)}")
        return f"Error sending verification code: {str(e)}"
