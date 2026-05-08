from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Attendance


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def save_attendance(request):
    """Save or update attendance records. Accepts list of {admno, date, status}."""
    institution_id = request.data.get('institution_id')
    records = request.data.get('records', [])
    if not institution_id or not records:
        return Response({'status': False, 'message': 'institution_id and records required'}, status=400)
    for rec in records:
        if not rec.get('status'):
            Attendance.objects.filter(
                institution_id=institution_id,
                admno=rec['admno'],
                date=rec['date']
            ).delete()
            continue
        Attendance.objects.update_or_create(
            institution_id=institution_id,
            admno=rec['admno'],
            date=rec['date'],
            defaults={'status': rec['status']}
        )
    return Response({'status': True, 'message': 'Saved'})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_attendance(request):
    """Get attendance for institution_id + year + month."""
    institution_id = request.GET.get('institution_id')
    year = request.GET.get('year')
    month = request.GET.get('month')
    if not institution_id or not year or not month:
        return Response({'status': False, 'message': 'institution_id, year, month required'}, status=400)

    try:
        year = int(year)
        month = int(month)
    except (TypeError, ValueError):
        return Response({'status': False, 'message': 'year and month must be valid numbers'}, status=400)

    records = Attendance.objects.filter(
        institution_id=institution_id,
        date__year=year,
        date__month=month
    ).values('admno', 'date', 'status').order_by('date', 'admno')

    data = [
        {
            'admno': record['admno'],
            'date': record['date'].isoformat(),
            'status': record['status'],
        }
        for record in records
    ]
    return Response({'status': True, 'records': data})
