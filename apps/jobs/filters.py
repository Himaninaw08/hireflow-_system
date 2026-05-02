import django_filters
from .models import Job

class JobFilter(django_filters.FilterSet):
    job_type = django_filters.MultipleChoiceFilter(choices=Job.JOB_TYPES)
    experience_level = django_filters.MultipleChoiceFilter(choices=Job.EXPERIENCE_LEVELS)
    salary_min = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    location = django_filters.CharFilter(lookup_expr='icontains')
    skills = django_filters.CharFilter(method='filter_skills')
    company = django_filters.CharFilter(field_name='company__name', lookup_expr='icontains')
    
    class Meta:
        model = Job
        fields = ['job_type', 'experience_level', 'location', 'skills', 'company']
    
    def filter_skills(self, queryset, name, value):
        if value:
            skills = [skill.strip() for skill in value.split(',')]
            for skill in skills:
                queryset = queryset.filter(skills_required__icontains=skill)
        return queryset
