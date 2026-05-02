from django.db import models
from django.utils.text import slugify
from apps.accounts.models import CustomUser

class CandidateProfile(models.Model):
    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level (0-2 years)'),
        ('junior', 'Junior (2-5 years)'),
        ('mid', 'Mid Level (5-8 years)'),
        ('senior', 'Senior (8-12 years)'),
        ('lead', 'Lead (12+ years)'),
    ]

    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
    ]

    WORK_PREFERENCES = [
        ('office', 'Office Only'),
        ('remote', 'Remote Only'),
        ('hybrid', 'Hybrid'),
        ('flexible', 'Flexible'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='candidate_profile')
    
    # Basic Information
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    portfolio_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    
    # Professional Information
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, blank=True)
    current_position = models.CharField(max_length=200, blank=True)
    current_company = models.CharField(max_length=200, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, blank=True)
    
    # Preferences
    work_preference = models.CharField(max_length=20, choices=WORK_PREFERENCES, blank=True)
    salary_expectation_min = models.PositiveIntegerField(null=True, blank=True)
    salary_expectation_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='USD')
    available_from = models.DateField(null=True, blank=True)
    open_to_relocation = models.BooleanField(default=True)
    
    # Skills and Expertise
    skills = models.JSONField(default=list)
    languages = models.JSONField(default=list)  # [{language: 'English', proficiency: 'Fluent'}]
    certifications = models.JSONField(default=list)  # [{name: 'AWS Certified', issuer: 'Amazon', date: '2023-01-01'}]
    
    # Resume and Documents
    resume_file = models.FileField(upload_to='resumes/', null=True, blank=True)
    cover_letter_file = models.FileField(upload_to='cover_letters/', null=True, blank=True)
    
    # Social and Visibility
    is_public = models.BooleanField(default=True)
    is_active_job_seeker = models.BooleanField(default=True)
    profile_completion_percentage = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.full_name or self.user.email} Profile"

    def save(self, *args, **kwargs):
        # Calculate profile completion percentage
        completion_fields = [
            'headline', 'bio', 'location', 'experience_level',
            'current_position', 'employment_type', 'work_preference',
            'skills', 'languages', 'resume_file'
        ]
        
        completed = 0
        for field in completion_fields:
            value = getattr(self, field)
            if value:
                if isinstance(value, list) and len(value) > 0:
                    completed += 1
                elif not isinstance(value, list):
                    completed += 1
        
        self.profile_completion_percentage = int((completed / len(completion_fields)) * 100)
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return self.user.full_name or self.user.email

    @property
    def email(self):
        return self.user.email

    @property
    def salary_range(self):
        if self.salary_expectation_min and self.salary_expectation_max:
            return f"{self.salary_currency} {self.salary_expectation_min:,} - {self.salary_expectation_max:,}"
        elif self.salary_expectation_min:
            return f"{self.salary_currency} {self.salary_expectation_min:,}+"
        elif self.salary_expectation_max:
            return f"Up to {self.salary_currency} {self.salary_expectation_max:,}"
        return "Not specified"

class CandidateExperience(models.Model):
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
    ]

    profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='experiences')
    
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES)
    location = models.CharField(max_length=200, blank=True)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # null for current position
    is_current_position = models.BooleanField(default=False)
    
    description = models.TextField(blank=True)
    achievements = models.JSONField(default=list)  # List of achievements
    technologies_used = models.JSONField(default=list)  # List of technologies
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.position} at {self.company}"

    @property
    def duration_years(self):
        from datetime import date
        end = self.end_date or date.today()
        start = self.start_date
        
        years = (end.year - start.year) - ((end.month, end.day) < (start.month, start.day))
        months = (end.month - start.month) if (end.day >= start.day) else (end.month - start.month - 12)
        if end.day < start.day:
            months += 12
            years -= 1
        
        total_months = years * 12 + months
        return total_months / 12

class CandidateEducation(models.Model):
    EDUCATION_LEVELS = [
        ('high_school', 'High School'),
        ('associate', 'Associate Degree'),
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('phd', 'PhD'),
        ('other', 'Other'),
    ]

    profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='education')
    
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200)
    education_level = models.CharField(max_length=20, choices=EDUCATION_LEVELS)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # null for ongoing
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    description = models.TextField(blank=True)
    achievements = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} from {self.institution}"

class CandidateProject(models.Model):
    PROJECT_TYPES = [
        ('personal', 'Personal Project'),
        ('academic', 'Academic Project'),
        ('work', 'Work Project'),
        ('open_source', 'Open Source'),
    ]

    profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='projects')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)
    
    technologies = models.JSONField(default=list)
    live_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # null for ongoing
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-start_date']

    def __str__(self):
        return self.title

class CandidateSkill(models.Model):
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='skill_details')
    
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=SKILL_LEVELS)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-years_of_experience', 'name']
        unique_together = ['profile', 'name']

    def __str__(self):
        return f"{self.name} ({self.level})"
