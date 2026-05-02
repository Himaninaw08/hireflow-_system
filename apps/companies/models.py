from django.db import models
from django.utils.text import slugify
from apps.accounts.models import CustomUser

class Company(models.Model):
    SUBSCRIPTION_TIERS = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    COMPANY_SIZES = [
        ('1-10', '1-10'),
        ('11-50', '11-50'),
        ('51-200', '51-200'),
        ('201-500', '201-500'),
        ('500+', '500+'),
    ]

    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_companies')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZES, blank=True)
    location = models.CharField(max_length=200, blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_TIERS, default='free')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure unique slug
            original_slug = self.slug
            counter = 1
            while Company.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def job_count(self):
        return self.jobs.count()

    @property
    def active_job_count(self):
        return self.jobs.filter(status='published').count()

class CompanyMember(models.Model):
    ROLES = [
        ('owner', 'Owner'),
        ('recruiter', 'Recruiter'),
        ('viewer', 'Viewer'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='company_memberships')
    role = models.CharField(max_length=20, choices=ROLES)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['company', 'user']
        ordering = ['role', 'joined_at']

    def __str__(self):
        return f"{self.user.email} - {self.company.name} ({self.role})"

    @property
    def is_owner(self):
        return self.role == 'owner'

    @property
    def can_manage_jobs(self):
        return self.role in ['owner', 'recruiter']

    @property
    def can_view_analytics(self):
        return self.role in ['owner', 'recruiter']
