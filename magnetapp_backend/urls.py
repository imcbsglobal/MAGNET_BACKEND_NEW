from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('student_data/', include('student_data.urls')),
    path('fee_pending/', include('fee_pending.urls')),
    path('api/fee_pending/', include('fee_pending.urls')),
    path('feepaid/', include('feepaid.urls')),
    path('api/feepaid/', include('feepaid.urls')),
    path('api/job-categories/', include('job_categories.urls')),
    path('api/teachers/', include('teachers_manage.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('api/calendar/', include('calendar_setup.urls')),
    path('api/id-card/', include('id_card.urls')),
    path('api/chat/', include('chat.urls')),
    path('id-card/', include('id_card.urls')),
    path('api/', include('add_administrators.urls')),
    path('api/', include('logins.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
