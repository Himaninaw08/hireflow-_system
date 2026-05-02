import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.jobs.models import Job, Application
from apps.pipeline.models import Pipeline, PipelineStage, StageTransition

User = get_user_model()

def create_pipeline_test_data():
    print("Creating pipeline test data...")
    
    # Get existing users and company
    try:
        employer = User.objects.get(email='employer@demo.com')
        candidate = User.objects.get(email='candidate@demo.com')
        company = Company.objects.get(name='Tech Corp')
        print("Found existing users and company")
    except (User.DoesNotExist, Company.DoesNotExist) as e:
        print(f"Missing data: {e}")
        print("Please run the previous test data creation script first")
        return
    
    # Create default pipeline
    try:
        pipeline = Pipeline.objects.get(company=company, is_default=True)
        print("Default pipeline already exists")
    except Pipeline.DoesNotExist:
        pipeline = Pipeline.objects.create(
            company=company,
            name='Default Recruitment Pipeline',
            is_default=True
        )
        print("Created default pipeline")
    
    # Create pipeline stages
    stage_configs = [
        {'name': 'Applied', 'color': '#6366f1', 'order': 0},
        {'name': 'Screening', 'color': '#8b5cf6', 'order': 1},
        {'name': 'Technical Interview', 'color': '#3b82f6', 'order': 2},
        {'name': 'Final Interview', 'color': '#10b981', 'order': 3},
        {'name': 'Offer', 'color': '#f59e0b', 'order': 4},
        {'name': 'Rejected', 'color': '#ef4444', 'order': 5},
    ]
    
    created_stages = []
    for stage_config in stage_configs:
        try:
            stage = PipelineStage.objects.get(
                pipeline=pipeline,
                name=stage_config['name']
            )
            print(f"Stage '{stage_config['name']}' already exists")
        except PipelineStage.DoesNotExist:
            stage = PipelineStage.objects.create(
                pipeline=pipeline,
                **stage_config
            )
            print(f"Created stage: {stage_config['name']}")
        created_stages.append(stage)
    
    # Get or create test jobs
    try:
        job = Job.objects.get(company=company, title='Senior Frontend Developer')
        print("Found existing job")
    except Job.DoesNotExist:
        print("No job found. Please run the previous test data creation script first")
        return
    
    # Create test applications with different stages
    application_data = [
        {
            'candidate': candidate,
            'job': job,
            'status': 'applied',
            'stage_index': 0,  # Applied
            'cover_letter': 'I am very interested in this position and believe my skills align perfectly with your requirements.'
        },
        {
            'candidate': candidate,
            'job': job,
            'status': 'screening',
            'stage_index': 1,  # Screening
            'cover_letter': 'I have 5 years of experience in frontend development and have worked on similar projects.'
        },
        {
            'candidate': candidate,
            'job': job,
            'status': 'interview',
            'stage_index': 2,  # Technical Interview
            'cover_letter': 'I am excited about the opportunity to join your team and contribute to your success.'
        },
    ]
    
    for i, app_data in enumerate(application_data):
        try:
            # Create a new candidate for each application
            candidate_email = f'candidate{i+2}@demo.com'
            try:
                test_candidate = User.objects.get(email=candidate_email)
            except User.DoesNotExist:
                test_candidate = User.objects.create_user(
                    email=candidate_email,
                    password='demo123',
                    first_name=f'Test',
                    last_name=f'Candidate {i+2}',
                    role='candidate'
                )
            
            application = Application.objects.create(
                candidate=test_candidate,
                job=job,
                status=app_data['status'],
                cover_letter=app_data['cover_letter'],
                is_anonymous=i % 2 == 0  # Every other application is anonymous
            )
            
            # Set pipeline stage
            if app_data['stage_index'] < len(created_stages):
                application.pipeline_stage = created_stages[app_data['stage_index']]
                application.save()
                
                # Create initial transition
                StageTransition.objects.create(
                    application=application,
                    from_stage=None,
                    to_stage=created_stages[app_data['stage_index']],
                    moved_by=employer,
                    note=f'Application created and moved to {created_stages[app_data['stage_index']].name}'
                )
            
            print(f"Created application {i+1} in stage: {created_stages[app_data['stage_index']].name}")
            
        except Exception as e:
            print(f"Error creating application {i+1}: {e}")
    
    print("\nPipeline test data creation complete!")
    print("\nTest credentials:")
    print("Employer: employer@demo.com / demo123")
    print("Candidates: candidate@demo.com / demo123, candidate2@demo.com / demo123, etc.")
    print("\nPipeline features to test:")
    print("1. Drag and drop applications between stages")
    print("2. Click on applications to view details")
    print("3. Select multiple applications for bulk actions")
    print("4. View application timeline")
    print("5. Test anonymous application reveal")

if __name__ == '__main__':
    create_pipeline_test_data()
