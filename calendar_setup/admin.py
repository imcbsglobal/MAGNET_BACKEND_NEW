from django.contrib import admin
from .models import CalendarEvent

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ['institution_id', 'date', 'event_type', 'title', 'is_active']
    list_filter = ['event_type', 'is_active', 'institution_id']
    search_fields = ['institution_id', 'title', 'description']
    ordering = ['-date']
    date_hierarchy = 'date'
