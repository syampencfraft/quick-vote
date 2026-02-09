import random
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP

def generate_otp(user):
    code = str(random.randint(100000, 999999))
    OTP.objects.create(user=user, code=code)
    return code

def send_otp_email(user, otp_code):
    subject = 'Your Voting System OTP'
    message = f'Your OTP for verification is {otp_code}. It is valid for 10 minutes.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    
    # In development, fail_silently=True or mock if email settings aren't configured
    try:
        send_mail(subject, message, email_from, recipient_list)
        print(f"OTP sent to {user.email}: {otp_code}") # For dev monitoring
    except Exception as e:
        print(f"Error sending email: {e}")
