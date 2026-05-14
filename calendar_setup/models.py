from django.db import models

class CalendarEvent(models.Model):
    EVENT_TYPES = [
        ('H', 'Holiday'),
        ('L', 'Leave'),
        ('E', 'Event'),
    ]

    institution_id = models.CharField(max_length=100, help_text="Client/Institution ID")
    date = models.DateField(help_text="Date of the event")
    event_type = models.CharField(max_length=1, choices=EVENT_TYPES, default='H', help_text="Type of calendar event")
    title = models.CharField(max_length=200, help_text="Title/Name of the event")
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the event")
    is_active = models.BooleanField(default=True, help_text="Whether this event is active")

    class Meta:
        unique_together = ['institution_id', 'date']
        ordering = ['date']
        verbose_name = "Calendar Event"
        verbose_name_plural = "Calendar Events"

    def __str__(self):
        return f"{self.institution_id} - {self.date} - {self.title}"
