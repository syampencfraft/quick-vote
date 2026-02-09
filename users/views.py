from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import CustomUserCreationForm, OTPForm, StudentProfileForm
from .models import User, StudentProfile
from .utils_otp import generate_otp, send_otp_email
from .utils_face import get_face_encoding

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # Deactivate until OTP verified
            user.save()
            
            # Send OTP
            code = generate_otp(user)
            send_otp_email(user, code)
            
            # Store user ID in session for OTP verification
            request.session['verification_user_id'] = user.id
            messages.success(request, "Registration successful. Please verify OTP sent to your email.")
            return redirect('otp_verify')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def otp_verify_view(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        return redirect('login')
        
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['otp']
            try:
                user = User.objects.get(id=user_id)
                latest_otp = user.otp_set.order_by('-created_at').first()
                
                if latest_otp and latest_otp.code == code and latest_otp.is_valid():
                    user.is_active = True
                    user.is_verified = True
                    user.save()
                    del request.session['verification_user_id']
                    
                    login(request, user)
                    messages.success(request, "Email verified successfully!")
                    
                    if user.role == User.Role.VOTER:
                        return redirect('voter_profile')
                    return redirect('election_list')
                else:
                    messages.error(request, "Invalid or expired OTP.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
    else:
        form = OTPForm()
    return render(request, 'users/otp_verify.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.role == User.Role.VOTER and not hasattr(user, 'student_profile'):
                     return redirect('voter_profile')
                return redirect('election_list')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def voter_profile_view(request):
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES)
        if form.is_valid():
            # Process Face
            image_file = request.FILES.get('face_image')
            encoding = get_face_encoding(image_file)
            
            if encoding is None:
                messages.error(request, "Face not detected in the image. Please upload a clear photo.")
            else:
                profile = form.save(commit=False)
                profile.user = request.user
                profile.face_encoding = encoding
                profile.save()
                messages.success(request, "Profile completed! You are now enrolled.")
                return redirect('election_list')
    else:
        form = StudentProfileForm()
    return render(request, 'users/voter_profile.html', {'form': form})

@login_required
def dashboard_view(request):
    return render(request, 'users/dashboard.html')

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')
