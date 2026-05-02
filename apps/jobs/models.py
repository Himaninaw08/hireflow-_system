from django.db import models
from django.utils.text import slugify
from apps.companies.models import Company
from apps.accounts.models import CustomUser

class Job(models.Model):
    JOB_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
    ]

    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('lead', 'Lead Level'),
    ]

    STATUSES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_jobs')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250)
    description = models.TextField()  # stores rich HTML
    requirements = models.TextField(blank=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS)
    location = models.CharField(max_length=200, blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=10, default='INR')
    skills_required = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUSES, default='draft')
    is_anonymous_apply = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    apply_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.title} {self.company.name}")
            self.slug = base_slug
            # Ensure unique slug
            original_slug = self.slug
            counter = 1
            while Job.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def application_count(self):
        return self.applications.count()

    @property
    def salary_range(self):
        if self.salary_min and self.salary_max:
            return f"{self.currency} {self.salary_min:,} - {self.salary_max:,}"
        elif self.salary_min:
            return f"{self.currency} {self.salary_min:,}+"
        elif self.salary_max:
            return f"Up to {self.currency} {self.salary_max:,}"
        return "Not specified"

    @property
    def is_expired(self):
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_applications(self):
        self.apply_count += 1
        self.save(update_fields=['apply_count'])

class Application(models.Model):
    STATUSES = [
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('interview', 'Interview'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    pipeline_stage = models.ForeignKey(
        'pipeline.PipelineStage', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='applications'
    )
    status = models.CharField(max_length=20, choices=STATUSES, default='applied')
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField(blank=True)
    rejection_reason = models.CharField(max_length=200, blank=True)
    is_anonymous = models.BooleanField(default=False)
    in_talent_pool = models.BooleanField(default=False)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['job', 'candidate']
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.candidate.email} - {self.job.title}"

    @property
    def candidate_name(self):
        if self.is_anonymous:
            return f"Candidate #{self.id}"
        return self.candidate.full_name or self.candidate.email

    def check_duplicate_application(self):
        """Check for duplicate applications to same company within last 6 months"""
        from django.utils import timezone
        from datetime import timedelta
        
        six_months_ago = timezone.now() - timedelta(days=180)
        duplicates = Application.objects.filter(
            candidate=self.candidate,
            job__company=self.job.company,
            applied_at__gte=six_months_ago
        ).exclude(id=self.id)
        
        return duplicates.exists()

class Tag(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6366f1')
    applications = models.ManyToManyField(Application, blank=True, related_name='tags')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['company', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.company.name})"
