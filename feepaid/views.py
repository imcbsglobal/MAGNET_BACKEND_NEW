from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FeePaid

@csrf_exempt
def add_fee_paid(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if isinstance(data, list):
            if not data:
                return JsonResponse({'status': False, 'message': 'Empty data list'}, status=400)

            institution_ids = set(item.get('institution_id') for item in data if item.get('institution_id'))
            if institution_ids:
                FeePaid.objects.filter(institution_id__in=institution_ids).delete()

            fees = [
                FeePaid(
                    institution_id=item.get('institution_id'),
                    admno=item.get('admno'),
                    particulars=item.get('particulars'),
                    amount=item.get('amount'),
                    date=item.get('date'),
                    refno=item.get('refno'),
                    remark=item.get('remark')
                ) for item in data
            ]
            FeePaid.objects.bulk_create(fees)
            return JsonResponse({
                'status': True,
                'message': f'{len(fees)} fee paid records updated successfully'
            })
        else:
            institution_id = data.get('institution_id')
            if institution_id:
                FeePaid.objects.filter(institution_id=institution_id).delete()

            fee = FeePaid.objects.create(
                institution_id=institution_id,
                admno=data.get('admno'),
                particulars=data.get('particulars'),
                amount=data.get('amount'),
                date=data.get('date'),
                refno=data.get('refno'),
                remark=data.get('remark')
            )

            return JsonResponse({
                'status': True,
                'message': 'Fee paid updated successfully',
                'id': fee.id
            })