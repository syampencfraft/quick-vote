import random
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP


def generate_otp(user):
    code = str(random.randint(100000, 999999))
    OTP.objects.create(user=user, code=code)
    return code


def generate_otp_code():
    """Generate a 6-digit OTP code without saving to DB."""
    return str(random.randint(100000, 999999))


def send_otp_to_email(email, otp_code):
    """Send OTP to a raw email address (no User object required)."""
    subject = 'Your Voting System OTP'
    message = f'Your OTP for verification is {otp_code}. It is valid for 10 minutes.'
    email_from = settings.EMAIL_HOST_USER
    try:
        send_mail(subject, message, email_from, [email])
        print(f"[OTP] Sent to {email}")
    except Exception as e:
        print(f"[OTP EMAIL ERROR] Could not send email: {e}")
    # Always print OTP to console for easy development testing
    print(f"[DEV] OTP for {email}: {otp_code}")



def send_otp_email(user, otp_code):
    subject = 'Your Voting System OTP'
    message = f'Your OTP for verification is {otp_code}. It is valid for 10 minutes.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user.email]

    try:
        send_mail(subject, message, email_from, recipient_list)
    except Exception as e:
        print(f"Error sending email: {e}")

