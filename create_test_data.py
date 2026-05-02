import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company, CompanyMember
from apps.jobs.models import Job, Application

User = get_user_model()

def create_test_data():
    print("Creating test data...")
    
    # Create test users
    try:
        employer = User.objects.get(email='employer@demo.com')
        print("Employer user already exists")
    except User.DoesNotExist:
        employer = User.objects.create_user(
            email='employer@demo.com',
            password='demo123',
            first_name='John',
            last_name='Employer',
            role='employer'
        )
        print("Created employer user")
    
    try:
        candidate = User.objects.get(email='candidate@demo.com')
        print("Candidate user already exists")
    except User.DoesNotExist:
        candidate = User.objects.create_user(
            email='candidate@demo.com',
            password='demo123',
            first_name='Jane',
            last_name='Candidate',
            role='candidate'
        )
        print("Created candidate user")
    
    # Create company
    try:
        company = Company.objects.get(name='Tech Corp')
        print("Company already exists")
    except Company.DoesNotExist:
        company = Company.objects.create(
            owner=employer,
            name='Tech Corp',
            description='A leading technology company',
            website='https://techcorp.com',
            industry='Technology',
            company_size='51-200',
            subscription_tier='pro'
        )
        print("Created company")
    
    # Create test jobs
    job_data = [
        {
            'title': 'Senior Frontend Developer',
            'description': '<p>We are looking for an experienced Frontend Developer to join our team.</p><p>Requirements:</p><ul><li>5+ years of experience</li><li>React expertise</li><li>TypeScript knowledge</li></ul>',
            'requirements': '<p>Must have experience with React, TypeScript, and modern frontend technologies.</p>',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'location': 'San Francisco, CA',
            'salary_min': 120000,
            'salary_max': 180000,
            'currency': 'USD',
            'skills_required': ['React', 'TypeScript', 'JavaScript', 'CSS', 'HTML'],
            'status': 'published'
        },
        {
            'title': 'Backend Engineer',
            'description': '<p>Join our backend team to build scalable APIs and services.</p>',
            'requirements': '<p>Experience with Python, Django, and databases required.</p>',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'location': 'Remote',
            'salary_min': 80000,
            'salary_max': 120000,
            'currency': 'USD',
            'skills_required': ['Python', 'Django', 'PostgreSQL', 'Docker'],
            'status': 'published'
        },
        {
            'title': 'UX Designer',
            'description': '<p>We need a creative UX Designer to improve our user experience.</p>',
            'requirements': '<p>Portfolio required with experience in user research and design.</p>',
            'job_type': 'contract',
            'experience_level': 'mid',
            'location': 'New York, NY',
            'salary_min': 60,
            'salary_max': 80,
            'currency': 'USD',
            'skills_required': ['Figma', 'Adobe XD', 'User Research', 'Prototyping'],
            'status': 'draft'
        }
    ]
    
    for job_info in job_data:
        try:
            job = Job.objects.get(title=job_info['title'], company=company)
            print(f"Job '{job_info['title']}' already exists")
        except Job.DoesNotExist:
            job = Job.objects.create(
                company=company,
                created_by=employer,
                **job_info
            )
            print(f"Created job: {job_info['title']}")
    
    print("\nTest data creation complete!")
    print("\nLogin credentials:")
    print("Employer: employer@demo.com / demo123")
    print("Candidate: candidate@demo.com / demo123")

if __name__ == '__main__':
    create_test_data()
