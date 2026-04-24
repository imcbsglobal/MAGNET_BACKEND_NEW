from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FeePending

@csrf_exempt
def add_fee_pending(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if isinstance(data, list):
            if not data:
                return JsonResponse({'status': False, 'message': 'Empty data list'}, status=400)

            client_ids = set(item.get('client_id') for item in data if item.get('client_id'))
            if client_ids:
                FeePending.objects.filter(client_id__in=client_ids).delete()

            fees = [
                FeePending(
                    client_id=item.get('client_id'),
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
            client_id = data.get('client_id')
            if client_id:
                FeePending.objects.filter(client_id=client_id).delete()

            fee = FeePending.objects.create(
                client_id=client_id,
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