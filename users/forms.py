from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'mobile_number')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email address is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number')
        if not mobile:
            raise forms.ValidationError("Mobile number is required.")
        
        # Ensure it contains only digits and is exactly 10 characters long
        mobile = str(mobile).strip()
        if not mobile.isdigit():
            raise forms.ValidationError("Mobile number must contain only numbers.")
        
        if len(mobile) != 10:
            raise forms.ValidationError("Mobile number must be exactly 10 digits long.")
        
        return mobile

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6, label="Enter OTP")

class StudentProfileForm(forms.ModelForm):
    face_image = forms.ImageField(required=False, help_text="Capture a clear photo of your face for authentication.")
    
    class Meta:
        model = StudentProfile
        fields = ('roll_no', 'department')

    def clean_roll_no(self):
        roll_no = self.cleaned_data.get('roll_no')
        if not roll_no:
            raise forms.ValidationError("Voter ID is required.")
        
        # Ensure it's alphanumeric (no special characters)
        if not str(roll_no).isalnum():
            raise forms.ValidationError("Voter ID must contain only letters and numbers.")
        
        return roll_no

class EmailForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your registered email'})
    )


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'})
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        confirm = cleaned_data.get("confirm_password")

        if password and confirm and password != confirm:
            self.add_error('confirm_password', "Passwords do not match.")
        
        return cleaned_data
