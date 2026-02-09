from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Election, Candidate, Vote
from users.utils_face import compare_faces
from django.core.files.base import ContentFile
import base64


def first(request):
    return render(request, 'election/first_page.html')
    
def election_list(request):
    elections = Election.objects.filter(is_active=True)
    return render(request, 'election/index.html', {'elections': elections})

@login_required
def election_detail(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    candidates = election.candidates.all()
    
    # Check if already voted
    has_voted = Vote.objects.filter(election=election, voter=request.user).exists()
    
    return render(request, 'election/detail.html', {
        'election': election,
        'candidates': candidates,
        'has_voted': has_voted
    })

@login_required
def verify_face(request, election_id):
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
