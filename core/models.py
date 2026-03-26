from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import random
import string


# ── User Manager ─────────────────────────────────────────────────────
class SmartUserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user  = self.model(email=email, full_name=full_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None):
        user              = self.create_user(email, full_name, password)
        user.is_staff     = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# ── Custom User ───────────────────────────────────────────────────────
class SmartUser(AbstractBaseUser, PermissionsMixin):
    email       = models.EmailField(unique=True)
    full_name   = models.CharField(max_length=150)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['full_name']
    objects         = SmartUserManager()

    def __str__(self):
        return self.email


# ── User Profile ──────────────────────────────────────────────────────
class UserProfile(models.Model):
    EDUCATION_CHOICES = [
        ('none',      'No Formal Education'),
        ('primary',   'Primary School'),
        ('secondary', 'Secondary School'),
        ('graduate',  'Graduate'),
        ('postgrad',  'Post Graduate'),
    ]

    user           = models.OneToOneField(SmartUser, on_delete=models.CASCADE, related_name='profile')
    age            = models.PositiveIntegerField(null=True, blank=True)
    education      = models.CharField(max_length=20, choices=EDUCATION_CHOICES, blank=True)
    skills         = models.TextField(blank=True, help_text="Comma-separated skills")
    health_concern = models.TextField(blank=True)
    location       = models.CharField(max_length=100, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} — Profile"


# ── Government Schemes ────────────────────────────────────────────────
class GovernmentScheme(models.Model):
    CATEGORY_CHOICES = [
        ('Social Welfare & Empowerment', 'Social Welfare & Empowerment'),
        ('Education & Learning', 'Education & Learning'),
        ('Agriculture', 'Agriculture, Animal Husbandry & Fisheries'),
        ('Health & Wellness', 'Health & Wellness'),
        ('Business & Entrepreneurship', 'Business & Entrepreneurship'),
        ('Banking', 'Banking, Financial Services & Insurance'),
        ('Skills & Employment', 'Skills & Employment'),
        ('Other', 'Other Categories'),
    ]
    LEVEL_CHOICES = [
        ('Central', 'Central'),
        ('State', 'State'),
        ('Gram Panchayat', 'Gram Panchayat'),
    ]

    name        = models.CharField(max_length=200)
    description = models.TextField()
    category    = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    level       = models.CharField(max_length=50, choices=LEVEL_CHOICES, default='Central')
    
    # --- Bureaucratic Info ---
    ministry    = models.CharField(max_length=200, blank=True, null=True)
    state_name  = models.CharField(max_length=100, blank=True, null=True)  # Blank for Central
    
    # --- Demographic Targeting ---
    target_gender     = models.CharField(max_length=50, blank=True, null=True) # All, Male, Female
    target_caste      = models.CharField(max_length=50, blank=True, null=True) # General, SC/ST, OBC, All
    target_income     = models.CharField(max_length=50, blank=True, null=True) # BPL, APL, Any
    target_occupation = models.CharField(max_length=50, blank=True, null=True) # Student, Farmer, Entrepreneur, None

    eligibility = models.TextField()
    application_process = models.TextField(blank=True, null=True)
    link        = models.URLField(blank=True)
    is_active   = models.BooleanField(default=True)
    visits      = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ── Chat Messages ─────────────────────────────────────────────────────
class ChatMessage(models.Model):
    SENDER_CHOICES = [('user', 'User'), ('bot', 'Bot')]

    user       = models.ForeignKey(SmartUser, on_delete=models.CASCADE, related_name='chat_messages')
    sender     = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.message[:50]}"


# ── Job Recommendations ───────────────────────────────────────────────
class JobRecommendation(models.Model):
    user        = models.ForeignKey(SmartUser, on_delete=models.CASCADE, related_name='job_recommendations')
    title       = models.CharField(max_length=200)
    description = models.TextField()
    match_score = models.FloatField(default=0.0)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} → {self.user.email}"


# ── User Feedback ─────────────────────────────────────────────────────
class UserFeedback(models.Model):
    user          = models.ForeignKey(SmartUser, on_delete=models.CASCADE, related_name='feedbacks')
    feedback_text = models.TextField()
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.email}"


# ── Saved Schemes ─────────────────────────────────────────────────────
class SavedScheme(models.Model):
    user = models.ForeignKey(SmartUser, on_delete=models.CASCADE, related_name='saved_schemes')
    scheme = models.ForeignKey(GovernmentScheme, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'scheme')

    def __str__(self):
        return f"{self.user.email} saved {self.scheme.name}"


# ── Password Recovery ──────────────────────────────────────────────────
import uuid
import random
import string

def generate_otp():
    """Kept to prevent old migration files from throwing AttributeError"""
    return ''.join(random.choices(string.digits, k=6))

class PasswordResetToken(models.Model):
    user       = models.ForeignKey(SmartUser, on_delete=models.CASCADE, related_name='reset_tokens')
    token      = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"Reset Token for {self.user.email}"