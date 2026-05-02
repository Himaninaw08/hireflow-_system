from django.db import models
from django.utils import timezone
from apps.accounts.models import CustomUser
from apps.jobs.models import Application, Job

class Interview(models.Model):
    INTERVIEW_TYPES = [
        ('phone', 'Phone Screen'),
        ('video', 'Video Call'),
        ('technical', 'Technical Interview'),
        ('behavioral', 'Behavioral Interview'),
        ('panel', 'Panel Interview'),
        ('onsite', 'On-site Interview'),
        ('final', 'Final Interview'),
    ]

    STATUSES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    interviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='interviews_conducted')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='interviews')
    
    title = models.CharField(max_length=200)
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES, default='video')
    status = models.CharField(max_length=20, choices=STATUSES, default='scheduled')
    
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    
    location = models.CharField(max_length=200, blank=True)  # Physical location or meeting link
    meeting_link = models.URLField(blank=True)
    meeting_password = models.CharField(max_length=50, blank=True)
    
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)  # Internal notes for interviewers
    
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='interviews_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"{self.title} - {self.application.candidate.email}"

    @property
    def candidate(self):
        return self.application.candidate

    @property
    def is_past(self):
        return self.scheduled_at < timezone.now()

    @property
    def is_today(self):
        return self.scheduled_at.date() == timezone.now().date()

    @property
    def end_time(self):
        from datetime import timedelta
        return self.scheduled_at + timedelta(minutes=self.duration_minutes)

    def save(self, *args, **kwargs):
        # Auto-set job from application if not set
        if not self.job and self.application:
            self.job = self.application.job
        super().save(*args, **kwargs)

class InterviewSlot(models.Model):
    """Available time slots for interviews"""
    interviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='interview_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    max_interviews = models.PositiveIntegerField(default=1)
    is_booked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['interviewer', 'date', 'start_time']

    def __str__(self):
        return f"{self.interviewer.email} - {self.date} {self.start_time}"

    @property
    def is_available(self):
        if self.is_booked:
            return False
        
        # Check if time is in the past
        from datetime import datetime, time, date
        now = timezone.now()
        slot_datetime = datetime.combine(self.date, self.start_time)
        if slot_datetime < now:
            return False
        
        return True

    @property
    def time_range(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"

class InterviewFeedback(models.Model):
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]

    RECOMMENDATION_CHOICES = [
        ('strong_no', 'Strong No'),
        ('no', 'No'),
        ('maybe', 'Maybe'),
        ('yes', 'Yes'),
        ('strong_yes', 'Strong Yes'),
    ]

    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name='feedback')
    interviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    
    overall_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES)
    
    technical_skills = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    communication = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    problem_solving = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    cultural_fit = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)
    
    would_hire = models.BooleanField(default=False)
    next_steps = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback for {self.interview.title} by {self.interviewer.email}"

    @property
    def average_rating(self):
        ratings = [self.overall_rating]
        if self.technical_skills:
            ratings.append(self.technical_skills)
        if self.communication:
            ratings.append(self.communication)
        if self.problem_solving:
            ratings.append(self.problem_solving)
        if self.cultural_fit:
            ratings.append(self.cultural_fit)
        
        return sum(ratings) / len(ratings) if ratings else 0

class InterviewTemplate(models.Model):
    """Reusable interview templates with questions"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    interview_type = models.CharField(max_length=20, choices=Interview.INTERVIEW_TYPES)
    duration_minutes = models.PositiveIntegerField(default=60)
    
    questions = models.JSONField(default=list)  # List of question objects
    evaluation_criteria = models.JSONField(default=list)  # List of evaluation criteria
    
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='interview_templates')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        unique_together = ['company', 'title']

    def __str__(self):
        return f"{self.title} ({self.company.name})"
