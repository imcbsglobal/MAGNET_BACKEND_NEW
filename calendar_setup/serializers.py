from rest_framework import serializers
from .models import CalendarEvent

class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = ['id', 'institution_id', 'date', 'event_type', 'title', 'description', 'is_active']
        read_only_fields = ['id']