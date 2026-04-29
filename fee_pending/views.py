from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FeePending
from student_data.models import StudentData
import decimal

class DecimalDateEncoder(json.JSONEncoder):
    def default(self, obj):
        import datetime
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

@csrf_exempt
def add_fee_pending(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if isinstance(data, list):
            if not data:
                return JsonResponse({'status': False, 'message': 'Empty data list'}, status=400)

            institution_ids = set(item.get('institution_id') for item in data if item.get('institution_id'))
            if institution_ids:
                FeePending.objects.filter(institution_id__in=institution_ids).delete()

            fees = [
                FeePending(
                    institution_id=item.get('institution_id'),
                    admno=item.get('admno'),
                    month=item.get('month'),
                    particulars=item.get('particulars'),
                    amount=item.get('amount'),
                    date=item.get('date'),
                    fine=item.get('fine'),
                    refno=item.get('refno'),
                    remark=item.get('remark')
                ) for item in data
            ]
            FeePending.objects.bulk_create(fees)
            return JsonResponse({
                'status': True,
                'message': f'{len(fees)} fee pending records updated successfully'
            })
        else:
            institution_id = data.get('institution_id')
            if institution_id:
                FeePending.objects.filter(institution_id=institution_id).delete()

            fee = FeePending.objects.create(
                institution_id=institution_id,
                admno=data.get('admno'),
                month=data.get('month'),
                particulars=data.get('particulars'),
                amount=data.get('amount'),
                date=data.get('date'),
                fine=data.get('fine'),
                refno=data.get('refno'),
                remark=data.get('remark')
            )

            return JsonResponse({
                'status': True,
                'message': 'Fee pending updated successfully',
                'id': fee.id
            })
    
    return JsonResponse({'status': False, 'message': 'Only POST method allowed'}, status=405)


def get_fee_pending(request):
    if request.method == 'GET':
        institution_id = request.GET.get('institution_id')
        admno = request.GET.get('admno')

        if not institution_id or not admno:
            return JsonResponse({'status': False, 'message': 'institution_id and admno are required'}, status=400)

        fees = list(FeePending.objects.filter(institution_id=institution_id, admno=admno).values(
            'id', 'institution_id', 'admno', 'month', 'particulars', 'amount', 'date', 'fine', 'refno', 'remark'
        ).order_by('date'))

        student = StudentData.objects.filter(institution_id=institution_id, admno=admno).values('student_name').first()
        student_name = student['student_name'] if student else ''
        for fee in fees:
            fee['student_name'] = student_name

        total_due = sum([float(item['amount']) + float(item['fine']) for item in fees])

        return JsonResponse({
            'status': True,
            'fees': fees,
            'total_due': total_due,
        })

    return JsonResponse({'status': False, 'message': 'Only GET method allowed'}, status=405)


def get_all_pending_fees(request):
    if request.method == 'GET':
        institution_id = request.GET.get('institution_id')
        if not institution_id:
            return JsonResponse({'status': False, 'message': 'institution_id is required'}, status=400)

        fees = list(FeePending.objects.filter(institution_id=institution_id).values(
            'id', 'institution_id', 'admno', 'month', 'particulars', 'amount', 'date', 'fine', 'refno', 'remark'
        ).order_by('admno', 'date'))

        students = {s['admno']: s for s in StudentData.objects.filter(institution_id=institution_id).values('admno', 'student_name', 'student_class', 'div')}
        for fee in fees:
            s = students.get(fee['admno'], {})
            fee['student_name'] = s.get('student_name', '')
            fee['student_class'] = s.get('student_class', '')
            fee['div'] = s.get('div', '')

        return JsonResponse({'status': True, 'fees': fees}, encoder=DecimalDateEncoder)

    return JsonResponse({'status': False, 'message': 'Only GET method allowed'}, status=405)
