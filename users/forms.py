from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'mobile_number')

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6, label="Enter OTP")

class StudentProfileForm(forms.ModelForm):
    face_image = forms.ImageField(help_text="Upload a clear photo of your face for authentication.")
    
    class Meta:
        model = StudentProfile
        fields = ('roll_no', 'department')
