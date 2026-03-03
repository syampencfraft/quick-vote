from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        VOTER = "VOTER", "Voter"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.VOTER)
    mobile_number = models.CharField(max_length=10, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_no = models.CharField(max_length=20, unique=True, verbose_name="Voter ID")
    department = models.CharField(max_length=100)
    face_encoding = models.BinaryField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.roll_no}"

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        # Valid for 10 minutes
        return timezone.now() < self.created_at + timezone.timedelta(minutes=10)
