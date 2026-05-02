from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/companies/', include('apps.companies.urls')),
    path('api/v1/', include('apps.jobs.urls')),
    path('api/v1/pipeline/', include('apps.pipeline.urls')),
    path('api/v1/interviews/', include('apps.interviews.urls')),
    path('api/v1/candidates/', include('apps.candidates.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
