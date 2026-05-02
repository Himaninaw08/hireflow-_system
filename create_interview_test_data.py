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
from apps.pipeline.models import PipelineStage
from apps.interviews.models import Interview, InterviewSlot, InterviewFeedback, InterviewTemplate
from apps.candidates.models import CandidateProfile, CandidateExperience, CandidateEducation, CandidateProject, CandidateSkill
from datetime import date, timedelta, time, datetime

User = get_user_model()

def create_interview_test_data():
    print("Creating interview and candidate test data...")
    
    # Get existing data
    try:
        employer = User.objects.get(email='employer@demo.com')
        company = Company.objects.get(name='Tech Corp')
        job = Job.objects.get(company=company, title='Senior Frontend Developer')
        
        # Get existing applications
        applications = Application.objects.filter(job=job)
        if applications.count() < 2:
            print("Need at least 2 applications. Please run previous test data scripts first.")
            return
            
        print(f"Found {applications.count()} applications")
        
    except (User.DoesNotExist, Company.DoesNotExist, Job.DoesNotExist) as e:
        print(f"Missing data: {e}")
        print("Please run previous test data creation scripts first")
        return
    
    # Create interview templates
    template_data = [
        {
            'title': 'Technical Frontend Interview',
            'description': 'Comprehensive frontend development interview',
            'interview_type': 'technical',
            'duration_minutes': 60,
            'questions': [
                {
                    'question': 'Explain the difference between controlled and uncontrolled components in React',
                    'category': 'React',
                    'difficulty': 'medium'
                },
                {
                    'question': 'How do you optimize React application performance?',
                    'category': 'Performance',
                    'difficulty': 'hard'
                }
            ],
            'evaluation_criteria': [
                {'name': 'Technical Knowledge', 'weight': 40},
                {'name': 'Problem Solving', 'weight': 30},
                {'name': 'Communication', 'weight': 30}
            ]
        },
        {
            'title': 'Behavioral Interview',
            'description': 'Assess cultural fit and soft skills',
            'interview_type': 'behavioral',
            'duration_minutes': 45,
            'questions': [
                {
                    'question': 'Tell me about a time you had to work with a difficult team member',
                    'category': 'Teamwork',
                    'difficulty': 'medium'
                }
            ],
            'evaluation_criteria': [
                {'name': 'Communication', 'weight': 40},
                {'name': 'Cultural Fit', 'weight': 35},
                {'name': 'Problem Solving', 'weight': 25}
            ]
        }
    ]
    
    for template_info in template_data:
        try:
            template = InterviewTemplate.objects.get(
                company=company,
                title=template_info['title']
            )
            print(f"Interview template '{template_info['title']}' already exists")
        except InterviewTemplate.DoesNotExist:
            template = InterviewTemplate.objects.create(
                company=company,
                created_by=employer,
                **template_info
            )
            print(f"Created interview template: {template_info['title']}")
    
    # Create interview slots for the next week
    today = date.today()
    for days_ahead in range(7):
        slot_date = today + timedelta(days=days_ahead)
        
        # Create multiple time slots per day
        time_slots = [
            (time(9, 0), time(10, 0)),
            (time(10, 30), time(11, 30)),
            (time(14, 0), time(15, 0)),
            (time(15, 30), time(16, 30)),
            (time(17, 0), time(18, 0)),
        ]
        
        for start_time, end_time in time_slots:
            try:
                slot = InterviewSlot.objects.get(
                    interviewer=employer,
                    date=slot_date,
                    start_time=start_time
                )
            except InterviewSlot.DoesNotExist:
                slot = InterviewSlot.objects.create(
                    interviewer=employer,
                    date=slot_date,
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=60
                )
    
    print("Created interview slots for the next week")
    
    # Create interviews for applications
    applications_list = list(applications.all())[:2]  # Take first 2 applications
    
    for i, application in enumerate(applications_list):
        # Schedule interview for tomorrow at 10 AM
        tomorrow = today + timedelta(days=1)
        interview_datetime = datetime.combine(tomorrow, time(10, 0))
        
        try:
            interview = Interview.objects.create(
                application=application,
                interviewer=employer,
                job=job,
                title=f"{['Technical', 'Behavioral'][i]} Interview - {application.candidate.email}",
                interview_type=['technical', 'behavioral'][i],
                status='scheduled',
                scheduled_at=interview_datetime,
                duration_minutes=60,
                location='Video Call',
                meeting_link='https://zoom.us/j/123456789',
                meeting_password='ats123',
                description=f"Interview for {job.title} position",
                notes=f"Candidate applied via job posting",
                created_by=employer
            )
            
            # Update application pipeline stage to interview
            interview_stage = PipelineStage.objects.filter(
                pipeline__company=company,
                name='Technical Interview'
            ).first()
            
            if interview_stage:
                application.pipeline_stage = interview_stage
                application.save()
            
            print(f"Created interview for {application.candidate.email}")
            
            # Create feedback for completed interview (if i == 0)
            if i == 0:
                try:
                    feedback = InterviewFeedback.objects.create(
                        interview=interview,
                        interviewer=employer,
                        overall_rating=4,
                        recommendation='yes',
                        technical_skills=4,
                        communication=4,
                        problem_solving=3,
                        cultural_fit=4,
                        strengths='Strong technical skills, good communication',
                        weaknesses='Could improve on problem solving approach',
                        additional_notes='Good candidate overall',
                        would_hire=True,
                        next_steps='Proceed to final interview'
                    )
                    print(f"Created feedback for interview {interview.id}")
                except Exception as e:
                    print(f"Error creating feedback: {e}")
            
        except Exception as e:
            print(f"Error creating interview: {e}")
    
    # Create candidate profiles for test candidates
    for i, application in enumerate(applications_list):
        try:
            candidate = application.candidate
            
            # Create or update candidate profile
            profile, created = CandidateProfile.objects.get_or_create(
                user=candidate,
                defaults={
                    'headline': f'{"Frontend Developer" if i == 0 else "Full Stack Developer"}',
                    'bio': f'Passionate developer with {3 + i} years of experience in building web applications.',
                    'location': 'San Francisco, CA',
                    'portfolio_url': f'https://{candidate.email.split("@")[0]}.github.io',
                    'github_url': f'https://github.com/{candidate.email.split("@")[0]}',
                    'linkedin_url': f'https://linkedin.com/in/{candidate.email.split("@")[0]}',
                    'experience_level': ['mid', 'senior'][i],
                    'current_position': f'{"Senior Developer" if i == 0 else "Developer"}',
                    'current_company': 'Previous Company',
                    'employment_type': 'full_time',
                    'work_preference': 'hybrid',
                    'salary_expectation_min': 80000 + (i * 20000),
                    'salary_expectation_max': 120000 + (i * 20000),
                    'salary_currency': 'USD',
                    'available_from': today,
                    'open_to_relocation': True,
                    'skills': ['React', 'JavaScript', 'TypeScript', 'CSS', 'HTML', 'Node.js', 'Python'],
                    'languages': [
                        {'language': 'English', 'proficiency': 'Fluent'},
                        {'language': 'Spanish', 'proficiency': 'Basic'}
                    ],
                    'certifications': [
                        {
                            'name': 'AWS Certified Developer',
                            'issuer': 'Amazon Web Services',
                            'date': '2023-01-15'
                        }
                    ],
                    'is_public': True,
                    'is_active_job_seeker': True
                }
            )
            
            if not created:
                # Update existing profile
                for field, value in {
                    'headline': f'{"Frontend Developer" if i == 0 else "Full Stack Developer"}',
                    'bio': f'Passionate developer with {3 + i} years of experience in building web applications.',
                    'location': 'San Francisco, CA',
                    'experience_level': ['mid', 'senior'][i],
                    'current_position': f'{"Senior Developer" if i == 0 else "Developer"}',
                }.items():
                    setattr(profile, field, value)
                profile.save()
            
            print(f"{'Created' if created else 'Updated'} candidate profile for {candidate.email}")
            
            # Create experience
            experience, exp_created = CandidateExperience.objects.get_or_create(
                profile=profile,
                company='Tech Solutions Inc',
                position=f'{"Senior Frontend Developer" if i == 0 else "Full Stack Developer"}',
                defaults={
                    'employment_type': 'full_time',
                    'location': 'San Francisco, CA',
                    'start_date': today - timedelta(days=365 * (2 + i)),
                    'end_date': today - timedelta(days=30),
                    'is_current_position': False,
                    'description': f'Led development of {["frontend", "full-stack"]} applications',
                    'achievements': [
                        'Increased application performance by 40%',
                        'Led team of 5 developers'
                    ],
                    'technologies_used': ['React', 'TypeScript', 'Node.js', 'AWS']
                }
            )
            
            # Create education
            education, edu_created = CandidateEducation.objects.get_or_create(
                profile=profile,
                institution='University of Technology',
                degree='Bachelor of Science',
                field_of_study='Computer Science',
                defaults={
                    'education_level': 'bachelor',
                    'start_date': today - timedelta(days=365 * 6),
                    'end_date': today - timedelta(days=365 * 4),
                    'gpa': 3.5,
                    'description': 'Focused on software engineering and web development'
                }
            )
            
            # Create skills
            skills_to_create = [
                {'name': 'React', 'level': 'advanced', 'years_of_experience': 3 + i, 'is_primary': True},
                {'name': 'JavaScript', 'level': 'expert', 'years_of_experience': 4 + i, 'is_primary': True},
                {'name': 'TypeScript', 'level': 'advanced', 'years_of_experience': 2 + i, 'is_primary': False},
                {'name': 'CSS', 'level': 'advanced', 'years_of_experience': 4 + i, 'is_primary': False},
                {'name': 'Node.js', 'level': 'intermediate', 'years_of_experience': 2 + i, 'is_primary': False},
            ]
            
            for skill_data in skills_to_create:
                skill, skill_created = CandidateSkill.objects.get_or_create(
                    profile=profile,
                    name=skill_data['name'],
                    defaults=skill_data
                )
            
            # Create projects
            project, proj_created = CandidateProject.objects.get_or_create(
                profile=profile,
                title=f'{"E-commerce Platform" if i == 0 else "Task Management App"}',
                defaults={
                    'description': f'{"Full-featured e-commerce platform with payment integration" if i == 0 else "Collaborative task management application"}',
                    'project_type': 'personal',
                    'technologies': ['React', 'Node.js', 'MongoDB', 'Stripe'],
                    'github_url': f'https://github.com/{candidate.email.split("@")[0]}/project{i+1}',
                    'live_url': f'https://project{i+1}.example.com',
                    'start_date': today - timedelta(days=180),
                    'end_date': today - timedelta(days=90),
                    'is_featured': True
                }
            )
            
        except Exception as e:
            print(f"Error creating candidate profile for {application.candidate.email}: {e}")
    
    print("\nInterview and candidate test data creation complete!")
    print("\nTest features:")
    print("1. Interview scheduling and management")
    print("2. Interview feedback and evaluation")
    print("3. Candidate profile management")
    print("4. Time slot availability")
    print("5. Interview templates")
    print("\nTest credentials:")
    print("Employer: employer@demo.com / demo123")
    print("Candidates: candidate@demo.com / demo123, candidate2@demo.com / demo123")

if __name__ == '__main__':
    create_interview_test_data()
