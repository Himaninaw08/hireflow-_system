from django.db import models
from django.utils.text import slugify
from apps.companies.models import Company
from apps.accounts.models import CustomUser

class Pipeline(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='pipelines')
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=150)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']
        unique_together = ['company', 'slug']

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure unique slug within company
            original_slug = self.slug
            counter = 1
            while Pipeline.objects.filter(company=self.company, slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def stage_count(self):
        return self.stages.count()

    @property
    def total_applications(self):
        from apps.jobs.models import Application
        return Application.objects.filter(
            pipeline_stage__in=self.stages.all()
        ).count()

class PipelineStage(models.Model):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=7, default='#6366f1')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ['pipeline', 'name']

    def __str__(self):
        return f"{self.name} ({self.pipeline.name})"

    @property
    def application_count(self):
        return self.applications.count()

    @property
    def percentage_of_total(self):
        total = self.pipeline.total_applications
        if total == 0:
            return 0
        return round((self.application_count / total) * 100, 1)

class StageTransition(models.Model):
    application = models.ForeignKey(
        'jobs.Application', 
        on_delete=models.CASCADE, 
        related_name='transitions'
    )
    from_stage = models.ForeignKey(
        PipelineStage, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transitions_from'
    )
    to_stage = models.ForeignKey(
        PipelineStage, 
        on_delete=models.CASCADE,
        related_name='transitions_to'
    )
    moved_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    note = models.TextField(blank=True)
    duration_hours = models.PositiveIntegerField(null=True, blank=True)  # Time spent in previous stage
    moved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-moved_at']

    def __str__(self):
        from_stage_name = self.from_stage.name if self.from_stage else 'Applied'
        to_stage_name = self.to_stage.name if self.to_stage else 'Unknown'
        return f"{self.application.candidate.email}: {from_stage_name} → {to_stage_name}"

    def save(self, *args, **kwargs):
        # Calculate duration if we have a previous transition
        if self.from_stage:
            previous_transition = StageTransition.objects.filter(
                application=self.application,
                to_stage=self.from_stage
            ).order_by('-moved_at').first()
            
            if previous_transition:
                from datetime import datetime
                duration = self.moved_at - previous_transition.moved_at
                self.duration_hours = duration.total_seconds() / 3600
        
        super().save(*args, **kwargs)

class PipelineTemplate(models.Model):
    """Predefined pipeline templates that companies can use"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    stages_data = models.JSONField(default=list)  # List of stage configs
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def create_pipeline(self, company, name=None):
        """Create a new pipeline from this template"""
        pipeline_name = name or self.name
        pipeline = Pipeline.objects.create(
            company=company,
            name=pipeline_name,
            slug=slugify(pipeline_name)
        )
        
        for i, stage_data in enumerate(self.stages_data):
            PipelineStage.objects.create(
                pipeline=pipeline,
                name=stage_data['name'],
                order=i,
                color=stage_data.get('color', '#6366f1'),
                description=stage_data.get('description', '')
            )
        
        return pipeline
