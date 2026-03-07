from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from .forms import CustomUserCreationForm, OTPForm, StudentProfileForm, EmailForm, ResetPasswordForm
from .models import User, StudentProfile
from .utils_otp import generate_otp, send_otp_email, generate_otp_code, send_otp_to_email
from .utils_face import get_face_encoding
from django.core.files.base import ContentFile
import base64
import os


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Do NOT save the user yet — store registration data in session
            user = form.save(commit=False)

            # Generate OTP and store everything in the session
            otp_code = generate_otp_code()
            request.session['pending_registration'] = {
                'username': user.username,
                'email': user.email,
                'password': user.password,  # already hashed by form.save(commit=False)
                'mobile_number': user.mobile_number if hasattr(user, 'mobile_number') else '',
                'otp_code': otp_code,
                'otp_created_at': timezone.now().isoformat(),
            }

            # Send OTP to the provided email
            send_otp_to_email(user.email, otp_code)

            messages.success(request, "OTP sent to your email. Please verify to complete registration.")
            return redirect('otp_verify')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def otp_verify_view(request):
    pending = request.session.get('pending_registration')
    if not pending:
        # Fallback: legacy flow (existing user awaiting activation)
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
                        if user.role == User.Role.VOTER and not user.is_superuser:
                            return redirect('voter_profile')
                        return redirect('admin_dashboard')
                    else:
                        messages.error(request, "Invalid or expired OTP.")
                except User.DoesNotExist:
                    messages.error(request, "User not found.")
        else:
            form = OTPForm()
        return render(request, 'users/otp_verify.html', {'form': form})

    # --- New session-based flow ---
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['otp']
            stored_code = pending.get('otp_code')
            created_at_str = pending.get('otp_created_at')

            # Check expiry (10 minutes)
            otp_expired = True
            if created_at_str:
                created_at = timezone.datetime.fromisoformat(created_at_str)
                if timezone.is_naive(created_at):
                    created_at = timezone.make_aware(created_at)
                otp_expired = timezone.now() > created_at + timezone.timedelta(minutes=10)

            if entered_code == stored_code and not otp_expired:
                # OTP is valid — NOW create the user in the database
                user = User(
                    username=pending['username'],
                    email=pending['email'],
                    mobile_number=pending.get('mobile_number', ''),
                    role=User.Role.VOTER,
                    is_active=True,
                    is_verified=True,
                )
                user.password = pending['password']  # Assign pre-hashed password directly
                user.save()

                # Clean up session
                del request.session['pending_registration']

                login(request, user)
                messages.success(request, "Email verified successfully! Welcome to QuickVote.")
                return redirect('voter_profile')
            elif otp_expired:
                messages.error(request, "OTP has expired. Please register again.")
                del request.session['pending_registration']
                return redirect('register')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
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
                if user.role == User.Role.VOTER and not user.is_superuser and not hasattr(user, 'student_profile'):
                     return redirect('voter_profile')
                if user.role == User.Role.ADMIN or user.is_superuser:
                    return redirect('admin_dashboard')
                return redirect('election_list')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def voter_profile_view(request):
    # Admins and Superusers don't need a voter profile
    if request.user.role == User.Role.ADMIN or request.user.is_superuser:
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES)
        if form.is_valid():
            # Process Face
            image_data = request.POST.get('captured_image')
            image_file = None
            
            if image_data and ';base64,' in image_data:
                try:
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    image_file = ContentFile(base64.b64decode(imgstr), name=f'user_{request.user.id}_face.{ext}')
                except Exception as e:
                    messages.error(request, f"Error processing captured image: {str(e)}")
                    return render(request, 'users/voter_profile.html', {'form': form})
            else:
                image_file = request.FILES.get('face_image')
            
            if not image_file:
                messages.error(request, "No facial image provided. Please capture or upload a photo.")
                return render(request, 'users/voter_profile.html', {'form': form})

            encoding = get_face_encoding(image_file)
            
            if encoding is None:
                messages.error(request, "Face not detected in the image. Please try again with a clear photo.")
            else:
                profile = form.save(commit=False)
                profile.user = request.user
                profile.face_encoding = encoding
                profile.save()
                messages.success(request, "Profile completed! You are now enrolled.")
                
                # Explicitly delete temporary files if they exist on disk
                if image_file and hasattr(image_file, 'temporary_file_path'):
                    try:
                        os.remove(image_file.temporary_file_path())
                    except Exception as e:
                        print(f"Error deleting temp file: {e}")

                return redirect('election_list')
    else:
        form = StudentProfileForm()
    return render(request, 'users/voter_profile.html', {'form': form})

@login_required
def dashboard_view(request):
    if request.user.role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    return render(request, 'users/dashboard.html')

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


def forgot_password_view(request):
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Generate OTP and store in session for reset
                otp_code = generate_otp_code()
                request.session['reset_password'] = {
                    'email': email,
                    'otp_code': otp_code,
                    'otp_created_at': timezone.now().isoformat(),
                    'verified': False
                }
                
                send_otp_to_email(email, otp_code)
                messages.success(request, "OTP sent to your email. Please verify to reset your password.")
                return redirect('verify_reset_otp')
            except User.DoesNotExist:
                # Security: Don't reveal if email exists or not. Just say "If an account exists..."
                # But for UX in small apps, we just show error:
                messages.error(request, "No account found with this email address.")
    else:
        form = EmailForm()
    return render(request, 'users/forgot_password.html', {'form': form})


def verify_reset_otp_view(request):
    reset_data = request.session.get('reset_password')
    if not reset_data:
        messages.error(request, "Session expired. Please restart the password reset process.")
        return redirect('forgot_password')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['otp']
            stored_code = reset_data.get('otp_code')
            created_at_str = reset_data.get('otp_created_at')

            # Check expiry (10 minutes)
            otp_expired = True
            if created_at_str:
                created_at = timezone.datetime.fromisoformat(created_at_str)
                if timezone.is_naive(created_at):
                    created_at = timezone.make_aware(created_at)
                otp_expired = timezone.now() > created_at + timezone.timedelta(minutes=10)

            if entered_code == stored_code and not otp_expired:
                # Mark as verified in session
                reset_data['verified'] = True
                request.session.modified = True
                
                messages.success(request, "OTP verified! You can now reset your password.")
                return redirect('reset_password')
            elif otp_expired:
                messages.error(request, "OTP has expired. Please request a new one.")
                del request.session['reset_password']
                return redirect('forgot_password')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
    else:
        form = OTPForm()
    return render(request, 'users/verify_reset_otp.html', {'form': form, 'email': reset_data.get('email')})


def reset_password_view(request):
    reset_data = request.session.get('reset_password')
    
    # Check if they have verified the OTP
    if not reset_data or not reset_data.get('verified'):
        messages.error(request, "Unauthorized access. Please verify OTP first.")
        return redirect('forgot_password')
        
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            email = reset_data.get('email')
            
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                # Clean up session
                del request.session['reset_password']
                
                messages.success(request, "Password reset successfully! You can now log in.")
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, "User account not found.")
                return redirect('forgot_password')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'users/reset_password.html', {'form': form})
