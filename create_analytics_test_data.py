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
from datetime import timedelta, datetime
from apps.companies.models import Company
from apps.jobs.models import Job, Application
from apps.interviews.models import Interview
from apps.candidates.models import CandidateProfile
from apps.analytics.models import (
    AnalyticsData, DashboardWidget, Report, MetricDefinition,
    CompanyMetrics, UserActivity
)
from apps.notifications.models import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationChannel, NotificationDelivery
)

User = get_user_model()

def create_analytics_test_data():
    print("Creating analytics and notifications test data...")
    
    # Get existing data
    try:
        employer = User.objects.get(email='employer@demo.com')
        company = Company.objects.get(name='Tech Corp')
        job = Job.objects.get(company=company, title='Senior Frontend Developer')
        
        print(f"Found existing data for {company.name}")
        
    except (User.DoesNotExist, Company.DoesNotExist, Job.DoesNotExist) as e:
        print(f"Missing data: {e}")
        print("Please run previous test data creation scripts first")
        return
    
    # Create CompanyMetrics
    try:
        metrics = CompanyMetrics.objects.get(company=company)
        print("CompanyMetrics already exists")
    except CompanyMetrics.DoesNotExist:
        metrics = CompanyMetrics.objects.create(
            company=company,
            total_jobs=5,
            active_jobs=3,
            draft_jobs=1,
            closed_jobs=1,
            total_applications=25,
            pending_applications=8,
            screening_applications=6,
            interview_applications=4,
            offered_applications=2,
            rejected_applications=5,
            scheduled_interviews=4,
            completed_interviews=2,
            upcoming_interviews=2,
            total_candidates=20,
            active_candidates=15,
            avg_time_to_hire=21,
            offer_acceptance_rate=85.5,
            cost_per_hire=3500.00
        )
        print("Created CompanyMetrics")
    
    # Create MetricDefinitions
    metric_definitions = [
        {
            'name': 'Total Jobs',
            'description': 'Total number of job postings',
            'metric_type': 'count',
            'data_source': 'jobs',
            'unit': 'count'
        },
        {
            'name': 'Application Rate',
            'description': 'Applications per job',
            'metric_type': 'average',
            'data_source': 'applications',
            'unit': 'applications/job'
        },
        {
            'name': 'Interview Conversion Rate',
            'description': 'Percentage of applications that reach interview stage',
            'metric_type': 'percentage',
            'data_source': 'applications',
            'unit': '%'
        },
        {
            'name': 'Time to Hire',
            'description': 'Average days from application to hire',
            'metric_type': 'average',
            'data_source': 'applications',
            'unit': 'days'
        }
    ]
    
    for metric_def in metric_definitions:
        try:
            MetricDefinition.objects.get(name=metric_def['name'])
            print(f"MetricDefinition '{metric_def['name']}' already exists")
        except MetricDefinition.DoesNotExist:
            MetricDefinition.objects.create(**metric_def)
            print(f"Created MetricDefinition: {metric_def['name']}")
    
    # Create DashboardWidgets
    widgets = [
        {
            'name': 'Jobs Overview',
            'widget_type': 'metric_card',
            'position_x': 0,
            'position_y': 0,
            'width': 4,
            'height': 3,
            'config': {
                'title': 'Jobs Overview',
                'metrics': ['total_jobs', 'active_jobs', 'draft_jobs'],
                'colors': ['#3b82f6', '#10b981', '#f59e0b']
            },
            'data_source': 'company_metrics',
            'refresh_interval': 300
        },
        {
            'name': 'Applications Trend',
            'widget_type': 'line_chart',
            'position_x': 4,
            'position_y': 0,
            'width': 8,
            'height': 3,
            'config': {
                'title': 'Applications Over Time',
                'x_axis': 'date',
                'y_axis': 'count',
                'color': '#8b5cf6'
            },
            'data_source': 'analytics_data/applications',
            'refresh_interval': 600
        },
        {
            'name': 'Pipeline Distribution',
            'widget_type': 'pie_chart',
            'position_x': 0,
            'position_y': 3,
            'width': 6,
            'height': 3,
            'config': {
                'title': 'Pipeline Distribution',
                'colors': ['#6366f1', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']
            },
            'data_source': 'pipeline_stages',
            'refresh_interval': 300
        },
        {
            'name': 'Recent Activities',
            'widget_type': 'list',
            'position_x': 6,
            'position_y': 3,
            'width': 6,
            'height': 3,
            'config': {
                'title': 'Recent Activities',
                'limit': 10
            },
            'data_source': 'user_activities',
            'refresh_interval': 120
        }
    ]
    
    for widget_data in widgets:
        try:
            widget = DashboardWidget.objects.get(company=company, name=widget_data['name'])
            print(f"DashboardWidget '{widget_data['name']}' already exists")
        except DashboardWidget.DoesNotExist:
            DashboardWidget.objects.create(
                company=company,
                created_by=employer,
                **widget_data
            )
            print(f"Created DashboardWidget: {widget_data['name']}")
    
    # Create Reports
    reports = [
        {
            'name': 'Monthly Jobs Report',
            'report_type': 'jobs',
            'description': 'Monthly overview of all job postings and their performance',
            'filters': {
                'date_from': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'date_to': timezone.now().strftime('%Y-%m-%d')
            },
            'columns': ['title', 'status', 'job_type', 'experience_level', 'views_count', 'apply_count'],
            'format': 'excel',
            'is_template': True,
            'is_scheduled': True,
            'schedule_frequency': 'monthly'
        },
        {
            'name': 'Applications Analysis',
            'report_type': 'applications',
            'description': 'Detailed analysis of all applications received',
            'filters': {
                'date_from': (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'date_to': timezone.now().strftime('%Y-%m-%d')
            },
            'columns': ['candidate', 'job', 'status', 'applied_at', 'is_anonymous'],
            'group_by': 'status',
            'sort_by': 'applied_at',
            'format': 'csv',
            'is_template': False
        },
        {
            'name': 'Interview Performance',
            'report_type': 'interviews',
            'description': 'Interview scheduling and completion metrics',
            'filters': {
                'date_from': (timezone.now() - timedelta(days=14)).strftime('%Y-%m-%d'),
                'date_to': timezone.now().strftime('%Y-%m-%d')
            },
            'columns': ['candidate', 'job', 'interview_type', 'status', 'scheduled_at', 'interviewer'],
            'format': 'json',
            'is_template': False
        }
    ]
    
    for report_data in reports:
        try:
            report = Report.objects.get(company=company, name=report_data['name'])
            print(f"Report '{report_data['name']}' already exists")
        except Report.DoesNotExist:
            Report.objects.create(
                company=company,
                created_by=employer,
                **report_data
            )
            print(f"Created Report: {report_data['name']}")
    
    # Create UserActivity records
    activities = [
        {'activity_type': 'login', 'metadata': {'source': 'web'}},
        {'activity_type': 'job_view', 'object_type': 'job', 'object_id': job.id},
        {'activity_type': 'application_created', 'object_type': 'application'},
        {'activity_type': 'interview_scheduled', 'object_type': 'interview'},
        {'activity_type': 'pipeline_updated', 'object_type': 'pipeline'},
        {'activity_type': 'report_generated', 'object_type': 'report'},
        {'activity_type': 'profile_viewed', 'object_type': 'candidate'},
        {'activity_type': 'notification_sent', 'object_type': 'notification'},
    ]
    
    for i, activity_data in enumerate(activities):
        # Create activity for different times
        created_at = timezone.now() - timedelta(hours=i*2)
        
        UserActivity.objects.create(
            user=employer,
            company=company,
            created_at=created_at,
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0 (Test Browser)',
            **activity_data
        )
    
    print("Created UserActivity records")
    
    # Create NotificationChannels
    channels = [
        {
            'name': 'Email Notifications',
            'channel_type': 'email',
            'config': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True
            },
            'is_global': True
        },
        {
            'name': 'Push Notifications',
            'channel_type': 'push',
            'config': {
                'firebase_server_key': 'test_key',
                'firebase_project_id': 'test_project'
            },
            'is_global': True
        },
        {
            'name': 'Company Email',
            'channel_type': 'email',
            'config': {
                'from_email': 'noreply@techcorp.com',
                'from_name': 'TechCorp ATS'
            },
            'is_global': False
        }
    ]
    
    for channel_data in channels:
        try:
            channel = NotificationChannel.objects.get(
                name=channel_data['name'],
                company=company if not channel_data['is_global'] else None
            )
            print(f"NotificationChannel '{channel_data['name']}' already exists")
        except NotificationChannel.DoesNotExist:
            NotificationChannel.objects.create(
                company=company if not channel_data['is_global'] else None,
                **channel_data
            )
            print(f"Created NotificationChannel: {channel_data['name']}")
    
    # Create NotificationTemplates
    templates = [
        {
            'name': 'Application Received',
            'notification_type': 'application',
            'priority': 'medium',
            'title_template': 'New Application for {job_title}',
            'message_template': 'A new application has been received for the {job_title} position from {candidate_name}.',
            'auto_send_email': True,
            'auto_send_push': True
        },
        {
            'name': 'Interview Scheduled',
            'notification_type': 'interview',
            'priority': 'high',
            'title_template': 'Interview Scheduled: {job_title}',
            'message_template': 'Your interview for {job_title} has been scheduled for {interview_date} at {interview_time}.',
            'auto_send_email': True,
            'auto_send_push': True
        },
        {
            'name': 'Job Published',
            'notification_type': 'job',
            'priority': 'low',
            'title_template': 'Job Published: {job_title}',
            'message_template': 'The job posting "{job_title}" has been published and is now live.',
            'auto_send_email': False,
            'auto_send_push': True
        }
    ]
    
    for template_data in templates:
        try:
            template = NotificationTemplate.objects.get(
                company=company,
                name=template_data['name']
            )
            print(f"NotificationTemplate '{template_data['name']}' already exists")
        except NotificationTemplate.DoesNotExist:
            NotificationTemplate.objects.create(
                company=company,
                created_by=employer,
                **template_data
            )
            print(f"Created NotificationTemplate: {template_data['name']}")
    
    # Create NotificationPreferences for employer
    try:
        preferences = NotificationPreference.objects.get(user=employer)
        print("NotificationPreferences already exists for employer")
    except NotificationPreference.DoesNotExist:
        NotificationPreference.objects.create(
            user=employer,
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
        print("Created NotificationPreferences for employer")
    
    # Create sample notifications
    notifications = [
        {
            'title': 'New Application Received',
            'message': 'A new application has been received for Senior Frontend Developer position.',
            'notification_type': 'application',
            'priority': 'medium',
            'object_type': 'application',
            'metadata': {'candidate_email': 'candidate@demo.com'}
        },
        {
            'title': 'Interview Tomorrow',
            'message': 'You have an interview scheduled for tomorrow at 10:00 AM.',
            'notification_type': 'interview',
            'priority': 'high',
            'object_type': 'interview',
            'metadata': {'interview_time': '10:00 AM'}
        },
        {
            'title': 'Job Published Successfully',
            'message': 'Your job posting "Senior Frontend Developer" has been published successfully.',
            'notification_type': 'job',
            'priority': 'low',
            'object_type': 'job',
            'metadata': {'job_title': 'Senior Frontend Developer'}
        },
        {
            'title': 'Pipeline Update',
            'message': '3 applications have moved to the interview stage.',
            'notification_type': 'pipeline',
            'priority': 'medium',
            'object_type': 'pipeline',
            'metadata': {'stage': 'interview', 'count': 3}
        }
    ]
    
    for i, notification_data in enumerate(notifications):
        created_at = timezone.now() - timedelta(hours=i*3)
        
        notification = Notification.objects.create(
            recipient=employer,
            sender=employer,
            company=company,
            created_at=created_at,
            **notification_data
        )
        
        # Mark some as read
        if i > 1:
            notification.is_read = True
            notification.read_at = created_at + timedelta(hours=1)
            notification.save()
        
        print(f"Created notification: {notification.title}")
    
    # Create NotificationDelivery records
    notifications_list = Notification.objects.filter(recipient=employer)
    channels = NotificationChannel.objects.all()
    
    for notification in notifications_list:
        for channel in channels[:2]:  # Create for first 2 channels
            NotificationDelivery.objects.create(
                notification=notification,
                channel=channel,
                status='sent' if notification.is_read else 'pending',
                sent_at=notification.created_at + timedelta(minutes=5),
                delivered_at=notification.created_at + timedelta(minutes=10) if notification.is_read else None
            )
    
    print("Created NotificationDelivery records")
    
    # Create AnalyticsData for the last 7 days
    today = timezone.now().date()
    for days_ago in range(7):
        date = today - timedelta(days=days_ago)
        
        # Jobs data
        AnalyticsData.objects.update_or_create(
            company=company,
            metric_type='jobs',
            metric_name='total_jobs',
            date=date,
            defaults={'value': 5}
        )
        
        AnalyticsData.objects.update_or_create(
            company=company,
            metric_type='jobs',
            metric_name='active_jobs',
            date=date,
            defaults={'value': 3}
        )
        
        # Applications data
        AnalyticsData.objects.update_or_create(
            company=company,
            metric_type='applications',
            metric_name='total_applications',
            date=date,
            defaults={'value': 25 + days_ago}
        )
        
        AnalyticsData.objects.update_or_create(
            company=company,
            metric_type='applications',
            metric_name='new_applications',
            date=date,
            defaults={'value': max(1, 5 - days_ago)}
        )
    
    print("Created AnalyticsData for the last 7 days")
    
    print("\nAnalytics and Notifications test data creation complete!")
    print("\nTest features:")
    print("1. Analytics dashboard with widgets")
    print("2. Custom reports generation")
    print("3. Real-time notifications")
    print("4. Notification templates and preferences")
    print("5. User activity tracking")
    print("6. Company metrics and KPIs")
    print("\nTest credentials:")
    print("Employer: employer@demo.com / demo123")

if __name__ == '__main__':
    create_analytics_test_data()
