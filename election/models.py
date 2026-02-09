from django.db import models
from users.models import User, StudentProfile

class Election(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    symbol = models.ImageField(upload_to='candidates/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.election.title})"

class Vote(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('election', 'voter')

    def __str__(self):
        return f"{self.voter.username} voted in {self.election.title}"

class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.name}"
