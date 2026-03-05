from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Election, Candidate, Vote
from users.utils_face import compare_faces
from django.core.files.base import ContentFile
import base64
import os
from django.contrib.auth.decorators import user_passes_test
from users.models import User
from .forms import ElectionForm, CandidateForm


def first(request):
    return render(request, 'election/first_page.html')
    
def election_list(request):
    if request.user.is_authenticated and request.user.role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    # Show both active and recently finished elections
    elections = Election.objects.all().order_by('-end_date')
    now = timezone.now()
    return render(request, 'election/index.html', {
        'elections': elections,
        'now': now
    })

@login_required
def election_detail(request, election_id):
    if request.user.role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    election = get_object_or_404(Election, pk=election_id)
    candidates = election.candidates.all()
    
    # Check if already voted
    has_voted = Vote.objects.filter(election=election, voter=request.user).exists()
    
    now = timezone.now()
    has_ended = now > election.end_date
    has_started = now >= election.start_date
    
    return render(request, 'election/detail.html', {
        'election': election,
        'candidates': candidates,
        'has_voted': has_voted,
        'has_ended': has_ended,
        'has_started': has_started
    })

@login_required
def verify_face(request, election_id):
    if request.user.role == User.Role.ADMIN:
        return JsonResponse({'success': False, 'message': 'Admins cannot participate in elections.'})
    if request.method == 'POST':
        image_data = request.POST.get('image')
        
        if not image_data:
            return JsonResponse({'success': False, 'message': 'No image data received.'})
            
        try:
            # Decode base64 image
            format, imgstr = image_data.split(';base64,') 
            ext = format.split('/')[-1] 
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
            
            # Get user's stored encoding
            if not hasattr(request.user, 'student_profile') or not request.user.student_profile.face_encoding:
                return JsonResponse({'success': False, 'message': 'No face encoding found for this user. Please complete your profile.'})

            known_encoding_bytes = request.user.student_profile.face_encoding
            
            # Compare
            # We need to reload the image from the ContentFile for face_recognition
            match = compare_faces(known_encoding_bytes, data)
            
            # Cleanup temporary file if it was written to disk
            if hasattr(data, 'temporary_file_path'):
                try:
                    os.remove(data.temporary_file_path())
                except:
                    pass

            if match:
                # Set a session flag to allow voting in this election
                request.session[f'verified_election_{election_id}'] = True
                return JsonResponse({'success': True, 'message': 'Verification successful!'})
            else:
                return JsonResponse({'success': False, 'message': 'Face verification failed. Please try again.'})
                
        except Exception as e:
            print(f"Error in detail: {e}")
            return JsonResponse({'success': False, 'message': f'Error processing image: {str(e)}'})
            
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

@login_required
def cast_vote(request, election_id):
    if request.user.role == User.Role.ADMIN:
        messages.error(request, "Admins cannot participate in elections.")
        return redirect('admin_dashboard')
    if request.method == 'POST':
        election = get_object_or_404(Election, pk=election_id)
        candidate_id = request.POST.get('candidate')
        
        # Security Checks
        if not request.session.get(f'verified_election_{election_id}'):
             messages.error(request, "Face verification required before voting.")
             return redirect('election_detail', election_id=election_id)
             
        if Vote.objects.filter(election=election, voter=request.user).exists():
             messages.error(request, "You have already voted in this election.")
             return redirect('election_detail', election_id=election_id)
        
        now = timezone.now()
        if now > election.end_date:
            messages.error(request, "This election has ended. Voting is no longer allowed.")
            return redirect('election_detail', election_id=election_id)
        
        if now < election.start_date:
            messages.error(request, "This election has not started yet.")
            return redirect('election_detail', election_id=election_id)
             
        # Record Vote
        candidate = get_object_or_404(Candidate, pk=candidate_id)
        Vote.objects.create(election=election, voter=request.user, candidate=candidate)
        
        # Clear session flag
        del request.session[f'verified_election_{election_id}']
        
        messages.success(request, "Vote cast successfully!")
        return redirect('election_results', election_id=election_id)
        
    return redirect('election_detail', election_id=election_id)

@login_required
def election_results(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    
    # Show results if:
    # 1. Admin manually published them
    # 2. The election has ended (deadline passed)
    # 3. User is an admin
    now = timezone.now()
    show_results = election.results_published or now > election.end_date or request.user.role == User.Role.ADMIN
    
    if not show_results:
        messages.warning(request, "Results for this election have not been published yet.")
        return redirect('election_list')
        
    candidates = election.candidates.all()
    
    results = []
    total_votes = Vote.objects.filter(election=election).count()
    
    for candidate in candidates:
        votes = Vote.objects.filter(election=election, candidate=candidate).count()
        percentage = (votes / total_votes * 100) if total_votes > 0 else 0
        results.append({
            'candidate': candidate,
            'votes': votes,
            'percentage': round(percentage, 1)
        })
    
    # Sort results by votes in descending order
    results.sort(key=lambda x: x['votes'], reverse=True)
        
    return render(request, 'election/results.html', {
        'election': election,
        'results': results,
        'total_votes': total_votes
    })

@login_required
@user_passes_test(lambda u: u.role == User.Role.ADMIN)
def admin_dashboard(request):
    elections = Election.objects.all().order_by('-start_date')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'election/admin_dashboard.html', {
        'elections': elections,
        'users': users
    })

@login_required
@user_passes_test(lambda u: u.role == User.Role.ADMIN)
def add_election(request):
    if request.method == 'POST':
        form = ElectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Election created successfully!")
            return redirect('admin_dashboard')
    else:
        form = ElectionForm()
    return render(request, 'election/election_form.html', {'form': form, 'title': 'Create New Election'})

@login_required
@user_passes_test(lambda u: u.role == User.Role.ADMIN)
def edit_election(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    if request.method == 'POST':
        form = ElectionForm(request.POST, instance=election)
        if form.is_valid():
            form.save()
            messages.success(request, "Election updated successfully!")
            return redirect('admin_dashboard')
    else:
        form = ElectionForm(instance=election)
    return render(request, 'election/election_form.html', {'form': form, 'title': 'Edit Election'})

@login_required
@user_passes_test(lambda u: u.role == User.Role.ADMIN)
def add_candidate(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.election = election
            candidate.save()
            messages.success(request, f"Candidate added to {election.title}")
            return redirect('admin_dashboard')
    else:
        form = CandidateForm()
    return render(request, 'election/candidate_form.html', {'form': form, 'election': election})

@login_required
@user_passes_test(lambda u: u.role == User.Role.ADMIN)
def toggle_election(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    election.is_active = not election.is_active
    election.save()
    status = "activated" if election.is_active else "deactivated"
    messages.success(request, f"Election {status} successfully!")
    return redirect('admin_dashboard')

@login_required
@user_passes_test(lambda u: u.role == User.Role.ADMIN)
def toggle_results(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    election.results_published = not election.results_published
    election.save()
    status = "published" if election.results_published else "hidden"
    messages.success(request, f"Election results are now {status}!")
    return redirect('admin_dashboard')

@login_required
@user_passes_test(lambda u: u.role == User.Role.ADMIN)
def finish_election(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    election.is_active = False
    election.results_published = True
    election.save()
    messages.success(request, f"Election '{election.title}' has been finished and results are now public!")
    return redirect('admin_dashboard')

def feedback_view(request):
    from .models import Feedback
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        Feedback.objects.create(name=name, email=email, message=message)
        messages.success(request, "Thank you for your feedback!")
        return redirect('dashboard')
    return render(request, 'election/feedback.html')
