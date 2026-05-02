import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime, date
from apps.companies.models import Company, CompanyMember
from apps.jobs.models import Job, Application, Tag
from apps.pipeline.models import Pipeline, PipelineStage, StageTransition
from apps.interviews.models import Interview, InterviewSlot, InterviewFeedback, InterviewTemplate
from apps.candidates.models import CandidateProfile, CandidateExperience, CandidateEducation, CandidateProject, CandidateSkill
from apps.analytics.models import AnalyticsData, DashboardWidget, Report, CompanyMetrics, UserActivity
from apps.notifications.models import Notification, NotificationTemplate, NotificationPreference, NotificationChannel

User = get_user_model()

def create_complete_test_data():
    print("Creating complete test data for Job Board ATS...")
    
    # Create users
    users_to_create = [
        {
            'email': 'admin@demo.com',
            'password': 'demo123',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin'
        },
        {
            'email': 'employer@demo.com',
            'password': 'demo123',
            'first_name': 'John',
            'last_name': 'Employer',
            'role': 'employer'
        },
        {
            'email': 'recruiter@demo.com',
            'password': 'demo123',
            'first_name': 'Jane',
            'last_name': 'Recruiter',
            'role': 'recruiter'
        },
        {
            'email': 'candidate@demo.com',
            'password': 'demo123',
            'first_name': 'Mike',
            'last_name': 'Candidate',
            'role': 'candidate'
        },
        {
            'email': 'candidate2@demo.com',
            'password': 'demo123',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'role': 'candidate'
        },
        {
            'email': 'candidate3@demo.com',
            'password': 'demo123',
            'first_name': 'David',
            'last_name': 'Smith',
            'role': 'candidate'
        }
    ]
    
    created_users = {}
    for user_data in users_to_create:
        try:
            user = User.objects.get(email=user_data['email'])
            print(f"User {user_data['email']} already exists")
        except User.DoesNotExist:
            user = User.objects.create_user(**user_data)
            print(f"Created user: {user_data['email']}")
        created_users[user_data['email']] = user
    
    # Create company
    try:
        company = Company.objects.get(name='Tech Corp')
        print("Company already exists")
    except Company.DoesNotExist:
        company = Company.objects.create(
            owner=created_users['employer@demo.com'],
            name='Tech Corp',
            description='A leading technology company specializing in innovative solutions',
            website='https://techcorp.com',
            industry='Technology',
            company_size='51-200',
            subscription_tier='pro'
        )
        print("Created company: Tech Corp")
    
    # Add company members
    company_members = [
        {'user': 'recruiter@demo.com', 'role': 'recruiter'},
    ]
    
    for member_data in company_members:
        try:
            member = CompanyMember.objects.get(company=company, user=created_users[member_data['user']])
            print(f"Company member {member_data['user']} already exists")
        except CompanyMember.DoesNotExist:
            CompanyMember.objects.create(
                company=company,
                user=created_users[member_data['user']],
                role=member_data['role']
            )
            print(f"Added company member: {member_data['user']}")
    
    # Create tags
    tags_data = [
        {'name': 'React', 'color': '#61dafb'},
        {'name': 'Python', 'color': '#3776ab'},
        {'name': 'JavaScript', 'color': '#f7df1e'},
        {'name': 'TypeScript', 'color': '#3178c6'},
        {'name': 'Node.js', 'color': '#339933'},
        {'name': 'Django', 'color': '#092e20'},
        {'name': 'AWS', 'color': '#ff9900'},
        {'name': 'Docker', 'color': '#2496ed'},
    ]
    
    for tag_data in tags_data:
        try:
            tag = Tag.objects.get(name=tag_data['name'])
            print(f"Tag {tag_data['name']} already exists")
        except Tag.DoesNotExist:
            Tag.objects.create(**tag_data)
            print(f"Created tag: {tag_data['name']}")
    
    # Create jobs
    jobs_data = [
        {
            'title': 'Senior Frontend Developer',
            'description': '<p>We are looking for an experienced Frontend Developer to join our team.</p><p><strong>Requirements:</strong></p><ul><li>5+ years of experience</li><li>React expertise</li><li>TypeScript knowledge</li></ul>',
            'requirements': '<p>Must have experience with React, TypeScript, and modern frontend technologies.</p>',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'location': 'San Francisco, CA',
            'salary_min': 120000,
            'salary_max': 180000,
            'currency': 'USD',
            'skills_required': ['React', 'TypeScript', 'JavaScript', 'CSS', 'HTML'],
            'status': 'published',
            'tags': ['React', 'TypeScript', 'JavaScript']
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
            'status': 'published',
            'tags': ['Python', 'Django', 'Docker']
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
            'status': 'draft',
            'tags': ['Figma', 'Adobe XD']
        },
        {
            'title': 'DevOps Engineer',
            'description': '<p>Help us build and maintain our cloud infrastructure.</p>',
            'requirements': '<p>Experience with AWS, Docker, and CI/CD pipelines.</p>',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'location': 'Remote',
            'salary_min': 130000,
            'salary_max': 170000,
            'currency': 'USD',
            'skills_required': ['AWS', 'Docker', 'Kubernetes', 'CI/CD'],
            'status': 'published',
            'tags': ['AWS', 'Docker', 'Kubernetes']
        }
    ]
    
    created_jobs = []
    for job_data in jobs_data:
        try:
            job = Job.objects.get(company=company, title=job_data['title'])
            print(f"Job '{job_data['title']}' already exists")
        except Job.DoesNotExist:
            # Get tag objects
            tag_objects = []
            if 'tags' in job_data:
                tag_objects = list(Tag.objects.filter(name__in=job_data['tags']))
            
            job = Job.objects.create(
                company=company,
                created_by=created_users['employer@demo.com'],
                **{k: v for k, v in job_data.items() if k != 'tags'}
            )
            job.tags.add(*tag_objects)
            print(f"Created job: {job_data['title']}")
        created_jobs.append(job)
    
    # Create pipeline
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
    
    # Create applications
    applications_data = [
        {
            'candidate_email': 'candidate@demo.com',
            'job_title': 'Senior Frontend Developer',
            'status': 'applied',
            'stage_index': 0,
            'cover_letter': 'I am very interested in this position and believe my skills align perfectly with your requirements.',
            'is_anonymous': False
        },
        {
            'candidate_email': 'candidate2@demo.com',
            'job_title': 'Senior Frontend Developer',
            'status': 'screening',
            'stage_index': 1,
            'cover_letter': 'I have 5 years of experience in frontend development and have worked on similar projects.',
            'is_anonymous': True
        },
        {
            'candidate_email': 'candidate3@demo.com',
            'job_title': 'Backend Engineer',
            'status': 'interview',
            'stage_index': 2,
            'cover_letter': 'I am excited about the opportunity to join your team and contribute to your success.',
            'is_anonymous': False
        },
        {
            'candidate_email': 'candidate@demo.com',
            'job_title': 'Backend Engineer',
            'status': 'applied',
            'stage_index': 0,
            'cover_letter': 'I have experience with Python and Django and would love to join your team.',
            'is_anonymous': False
        },
        {
            'candidate_email': 'candidate2@demo.com',
            'job_title': 'UX Designer',
            'status': 'applied',
            'stage_index': 0,
            'cover_letter': 'I have a strong portfolio in UX design and user research.',
            'is_anonymous': True
        }
    ]
    
    created_applications = []
    for app_data in applications_data:
        candidate = created_users[app_data['candidate_email']]
        job = next((j for j in created_jobs if j.title == app_data['job_title']), None)
        
        if not job:
            continue
            
        try:
            application = Application.objects.create(
                candidate=candidate,
                job=job,
                status=app_data['status'],
                cover_letter=app_data['cover_letter'],
                is_anonymous=app_data['is_anonymous']
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
                    moved_by=created_users['employer@demo.com'],
                    note=f'Application created and moved to {created_stages[app_data["stage_index"]].name}'
                )
            
            created_applications.append(application)
            print(f"Created application for {app_data['candidate_email']} - {app_data['job_title']}")
            
        except Exception as e:
            print(f"Error creating application: {e}")
    
    # Create interviews
    interviews_data = [
        {
            'application_index': 0,  # First application
            'title': 'Technical Frontend Interview',
            'interview_type': 'technical',
            'status': 'scheduled',
            'days_from_now': 1,
            'time': '10:00'
        },
        {
            'application_index': 2,  # Third application
            'title': 'Backend Technical Interview',
            'interview_type': 'technical',
            'status': 'completed',
            'days_from_now': -2,
            'time': '14:00'
        },
        {
            'application_index': 1,  # Second application
            'title': 'Frontend Screening Call',
            'interview_type': 'phone',
            'status': 'scheduled',
            'days_from_now': 2,
            'time': '11:30'
        }
    ]
    
    for interview_data in interviews_data:
        if interview_data['application_index'] >= len(created_applications):
            continue
            
        application = created_applications[interview_data['application_index']]
        
        # Calculate scheduled time
        days_offset = interview_data['days_from_now']
        interview_datetime = timezone.now() + timedelta(days=days_offset)
        hour, minute = map(int, interview_data['time'].split(':'))
        interview_datetime = interview_datetime.replace(hour=hour, minute=minute)
        
        try:
            interview = Interview.objects.create(
                application=application,
                interviewer=created_users['employer@demo.com'],
                job=application.job,
                title=interview_data['title'],
                interview_type=interview_data['interview_type'],
                status=interview_data['status'],
                scheduled_at=interview_datetime,
                duration_minutes=60,
                location='Video Call',
                meeting_link='https://zoom.us/j/123456789',
                meeting_password='ats123',
                description=f"Interview for {application.job.title} position",
                notes=f"Candidate applied via job posting",
                created_by=created_users['employer@demo.com']
            )
            
            # Create feedback for completed interviews
            if interview_data['status'] == 'completed':
                InterviewFeedback.objects.create(
                    interview=interview,
                    interviewer=created_users['employer@demo.com'],
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
            
            print(f"Created interview: {interview_data['title']}")
            
        except Exception as e:
            print(f"Error creating interview: {e}")
    
    # Create candidate profiles
    candidate_profiles_data = [
        {
            'email': 'candidate@demo.com',
            'headline': 'Senior Frontend Developer',
            'bio': 'Passionate frontend developer with 5 years of experience building modern web applications.',
            'location': 'San Francisco, CA',
            'experience_level': 'senior',
            'current_position': 'Senior Frontend Developer',
            'employment_type': 'full_time',
            'skills': ['React', 'TypeScript', 'JavaScript', 'CSS', 'HTML', 'Node.js'],
            'salary_min': 120000,
            'salary_max': 160000,
            'is_public': True,
            'is_active_job_seeker': True
        },
        {
            'email': 'candidate2@demo.com',
            'headline': 'Full Stack Developer',
            'bio': 'Versatile developer with experience in both frontend and backend technologies.',
            'location': 'New York, NY',
            'experience_level': 'mid',
            'current_position': 'Full Stack Developer',
            'employment_type': 'full_time',
            'skills': ['React', 'Node.js', 'Python', 'PostgreSQL', 'AWS'],
            'salary_min': 90000,
            'salary_max': 130000,
            'is_public': True,
            'is_active_job_seeker': True
        },
        {
            'email': 'candidate3@demo.com',
            'headline': 'Backend Engineer',
            'bio': 'Experienced backend developer specializing in Python and cloud technologies.',
            'location': 'Remote',
            'experience_level': 'senior',
            'current_position': 'Backend Engineer',
            'employment_type': 'full_time',
            'skills': ['Python', 'Django', 'AWS', 'Docker', 'PostgreSQL'],
            'salary_min': 110000,
            'salary_max': 150000,
            'is_public': True,
            'is_active_job_seeker': True
        }
    ]
    
    for profile_data in candidate_profiles_data:
        user = created_users[profile_data['email']]
        
        try:
            profile = CandidateProfile.objects.get(user=user)
            print(f"Candidate profile for {profile_data['email']} already exists")
        except CandidateProfile.DoesNotExist:
            profile = CandidateProfile.objects.create(
                user=user,
                **{k: v for k, v in profile_data.items() if k != 'email'}
            )
            print(f"Created candidate profile for {profile_data['email']}")
        
        # Create skills
        skills_data = [
            {'name': 'React', 'level': 'expert', 'years_of_experience': 5, 'is_primary': True},
            {'name': 'TypeScript', 'level': 'advanced', 'years_of_experience': 3, 'is_primary': True},
            {'name': 'JavaScript', 'level': 'expert', 'years_of_experience': 6, 'is_primary': False},
            {'name': 'Python', 'level': 'intermediate', 'years_of_experience': 2, 'is_primary': False},
        ]
        
        for skill_data in skills_data:
            if skill_data['name'] in profile_data['skills']:
                try:
                    skill = CandidateSkill.objects.get(profile=profile, name=skill_data['name'])
                except CandidateSkill.DoesNotExist:
                    skill = CandidateSkill.objects.create(
                        profile=profile,
                        **skill_data
                    )
    
    # Create company metrics
    try:
        metrics = CompanyMetrics.objects.get(company=company)
        print("CompanyMetrics already exists")
    except CompanyMetrics.DoesNotExist:
        CompanyMetrics.objects.create(
            company=company,
            total_jobs=len(created_jobs),
            active_jobs=len([j for j in created_jobs if j.status == 'published']),
            draft_jobs=len([j for j in created_jobs if j.status == 'draft']),
            closed_jobs=0,
            total_applications=len(created_applications),
            pending_applications=len([a for a in created_applications if a.status == 'applied']),
            screening_applications=len([a for a in created_applications if a.status == 'screening']),
            interview_applications=len([a for a in created_applications if a.status == 'interview']),
            offered_applications=0,
            rejected_applications=0,
            scheduled_interviews=len([i for i in Interview.objects.all() if i.status == 'scheduled']),
            completed_interviews=len([i for i in Interview.objects.all() if i.status == 'completed']),
            upcoming_interviews=len([i for i in Interview.objects.all() if i.status == 'scheduled' and i.scheduled_at > timezone.now()]),
            total_candidates=len(candidate_profiles_data),
            active_candidates=len([p for p in candidate_profiles_data if p['is_active_job_seeker']]),
            avg_time_to_hire=21,
            offer_acceptance_rate=85.5,
            cost_per_hire=3500.00
        )
        print("Created CompanyMetrics")
    
    # Create notification preferences for all users
    for user_email, user in created_users.items():
        if user.role in ['employer', 'recruiter', 'candidate']:
            try:
                NotificationPreference.objects.get(user=user)
                print(f"NotificationPreferences for {user_email} already exist")
            except NotificationPreference.DoesNotExist:
                NotificationPreference.objects.create(
                    user=user,
                    enable_email=True,
                    enable_push=True,
                    enable_in_app=True,
                    application_notifications=True,
                    interview_notifications=True,
                    job_notifications=True,
                    pipeline_notifications=True,
                    message_notifications=True,
                    system_notifications=True,
                    reminder_notifications=True,
                    alert_notifications=True,
                    quiet_hours_enabled=False,
                    daily_email_limit=20,
                    weekly_email_limit=100
                )
                print(f"Created NotificationPreferences for {user_email}")
    
    # Create notifications
    notifications_data = [
        {
            'recipient_email': 'employer@demo.com',
            'title': 'New Application Received',
            'message': 'A new application has been received for Senior Frontend Developer position.',
            'notification_type': 'application',
            'priority': 'medium',
            'object_type': 'application'
        },
        {
            'recipient_email': 'candidate@demo.com',
            'title': 'Interview Scheduled',
            'message': 'Your interview for Senior Frontend Developer has been scheduled.',
            'notification_type': 'interview',
            'priority': 'high',
            'object_type': 'interview'
        },
        {
            'recipient_email': 'employer@demo.com',
            'title': 'Job Published Successfully',
            'message': 'Your job posting "DevOps Engineer" has been published successfully.',
            'notification_type': 'job',
            'priority': 'low',
            'object_type': 'job'
        },
        {
            'recipient_email': 'recruiter@demo.com',
            'title': 'Pipeline Update',
            'message': '3 applications have moved to the interview stage.',
            'notification_type': 'pipeline',
            'priority': 'medium',
            'object_type': 'pipeline'
        }
    ]
    
    for notif_data in notifications_data:
        recipient = created_users[notif_data['recipient_email']]
        
        try:
            notification = Notification.objects.create(
                recipient=recipient,
                sender=created_users['employer@demo.com'],
                company=company,
                **{k: v for k, v in notif_data.items() if k != 'recipient_email'}
            )
            print(f"Created notification: {notif_data['title']}")
        except Exception as e:
            print(f"Error creating notification: {e}")
    
    # Create user activities
    activities_data = [
        {'user_email': 'employer@demo.com', 'activity_type': 'login'},
        {'user_email': 'employer@demo.com', 'activity_type': 'job_view', 'object_type': 'job'},
        {'user_email': 'candidate@demo.com', 'activity_type': 'application_created', 'object_type': 'application'},
        {'user_email': 'employer@demo.com', 'activity_type': 'interview_scheduled', 'object_type': 'interview'},
        {'user_email': 'recruiter@demo.com', 'activity_type': 'pipeline_updated', 'object_type': 'pipeline'},
    ]
    
    for i, activity_data in enumerate(activities_data):
        user = created_users[activity_data['user_email']]
        created_at = timezone.now() - timedelta(hours=i*2)
        
        UserActivity.objects.create(
            user=user,
            company=company,
            created_at=created_at,
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0 (Test Browser)',
            **{k: v for k, v in activity_data.items() if k != 'user_email'}
        )
    
    print("Created UserActivity records")
    
    print("\n" + "="*60)
    print("🎉 COMPLETE TEST DATA CREATION FINISHED!")
    print("="*60)
    print("\nTest Credentials:")
    print("├─ Admin: admin@demo.com / demo123")
    print("├─ Employer: employer@demo.com / demo123")
    print("├─ Recruiter: recruiter@demo.com / demo123")
    print("├─ Candidate: candidate@demo.com / demo123")
    print("├─ Candidate: candidate2@demo.com / demo123")
    print("└─ Candidate: candidate3@demo.com / demo123")
    
    print("\nSystem Overview:")
    print(f"├─ Company: {company.name}")
    print(f"├─ Jobs: {len(created_jobs)} ({len([j for j in created_jobs if j.status == 'published'])} published)")
    print(f"├─ Applications: {len(created_applications)}")
    print(f"├─ Interviews: {Interview.objects.count()}")
    print(f"├─ Pipeline Stages: {len(created_stages)}")
    print(f"├─ Candidate Profiles: {len(candidate_profiles_data)}")
    print(f"├─ Notifications: {Notification.objects.count()}")
    print(f"└─ User Activities: {UserActivity.objects.count()}")
    
    print("\nFeatures Ready for Testing:")
    print("✅ Phase 1: Authentication (All user roles)")
    print("✅ Phase 2: Jobs (Post, edit, manage job listings)")
    print("✅ Phase 3: Pipeline (Kanban board, application management)")
    print("✅ Phase 4: Interviews (Scheduling, feedback, candidate profiles)")
    print("✅ Phase 5: Analytics (Dashboard, reports, notifications)")
    
    print("\nNext Steps:")
    print("1. Run migrations: python manage.py makemigrations && python manage.py migrate")
    print("2. Start backend: python manage.py runserver")
    print("3. Start frontend: cd ../frontend && npm run dev")
    print("4. Test all features with the provided credentials")

if __name__ == '__main__':
    create_complete_test_data()
