from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import CalendarEvent
from .serializers import CalendarEventSerializer

class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = CalendarEvent.objects.filter(is_active=True)
        institution_id = self.request.query_params.get('institution_id')
        if institution_id:
            queryset = queryset.filter(institution_id=institution_id)
        return queryset

    @action(detail=False, methods=['get'])
    def by_month(self, request):
        """Get calendar events for a specific month and year"""
        institution_id = request.query_params.get('institution_id')
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if not all([institution_id, year, month]):
            return Response(
                {'error': 'institution_id, year, and month are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        events = self.get_queryset().filter(
            institution_id=institution_id,
            date__year=year,
            date__month=month,
        )

        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_year(self, request):
        """Get calendar events for a specific year"""
        institution_id = request.query_params.get('institution_id')
        year = request.query_params.get('year')

        if not all([institution_id, year]):
            return Response(
                {'error': 'institution_id and year are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        events = self.get_queryset().filter(
            institution_id=institution_id,
            date__year=year,
        )

        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create calendar events"""
        events_data = request.data.get('events', [])
        institution_id = request.data.get('institution_id')

        if not institution_id:
            return Response(
                {'error': 'institution_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_events = []
        for event_data in events_data:
            event_data['institution_id'] = institution_id
            serializer = self.get_serializer(data=event_data)
            if serializer.is_valid():
                serializer.save()
                created_events.append(serializer.data)
            else:
                return Response(
                    {'error': f'Invalid data for event: {serializer.errors}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(created_events, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def toggle_active(self, request, pk=None):
        """Toggle the active status of a calendar event"""
        event = self.get_object()
        event.is_active = not event.is_active
        event.save()
        serializer = self.get_serializer(event)
        return Response(serializer.data)
