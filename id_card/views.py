import json
import os
import re
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError

from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

from student_data.models import StudentData
from .models import IDCardForm


def _normalize_whatsapp_number(number):
    if not number:
        return None
    digits = re.sub(r'\D', '', str(number))
    if digits.startswith('0'):
        digits = digits.lstrip('0')
    if len(digits) == 10:
        digits = f'91{digits}'
    if len(digits) < 10:
        return None
    return digits


WHATSAPP_API_URL = 'https://app.dxing.in/api/send/whatsapp'
WHATSAPP_API_SECRET = '4d8911f61a3eff1123ba4b11408f66697ab8bdf5'
WHATSAPP_API_ACCOUNT = '1778132749812b4ba287f5ee0bc9d43bbf5bbe87fb69fc270dc7c77'


def _build_whatsapp_url(recipient, message):
    payload = {
        'secret': WHATSAPP_API_SECRET,
        'account': WHATSAPP_API_ACCOUNT,
        'recipient': recipient,
        'type': 'text',
        'message': message,
        'priority': '1',
    }
    return f"{WHATSAPP_API_URL}?{urlencode(payload)}"


def _send_whatsapp_message(recipient, message):
    if not recipient:
        raise ValueError('Recipient phone number is required')
    recipient = _normalize_whatsapp_number(recipient)
    if not recipient:
        raise ValueError('Recipient phone number is invalid')
    url = _build_whatsapp_url(recipient, message)
    try:
        with urlopen(url, timeout=20) as response:
            response.read()
        return True
    except URLError as exc:
        raise RuntimeError(str(exc))


def _build_parent_link(token):
    return f"https://magnetpro.in/id-card/form/{token}"


def _serialize_id_card(student, form=None):
    return {
        'institution_id': student.institution_id,
        'admno': student.admno,
        'student_name': student.student_name,
        'student_class': student.student_class,
        'div': student.div,
        'mobile': student.mobile,
        'fathername': student.fathername,
        'mothername': student.mothername,
        'address': student.address,
        'place': student.place,
        'remark': student.remark,
        'refno': student.refno,
        'link_token': form.token if form else None,
        'link_status': form.status if form else 'none',
        'parent_submitted': bool(form and form.status == IDCardForm.STATUS_USED),
        'details': {
            'student_name': form.student_name if form else '',
            'place': form.place if form else '',
            'district': form.district if form else '',
            'city': form.city if form else '',
            'state': form.state if form else '',
            'pin': form.pin if form else '',
            'phone': form.phone if form else '',
            'email': form.email if form else '',
            'father_name': form.father_name if form else '',
            'mother_name': form.mother_name if form else '',
            'dob': form.dob.isoformat() if form and form.dob else '',
        },
        'form_id': form.id if form else None,
        'sent_at': form.sent_at.isoformat() if form and form.sent_at else None,
        'used_at': form.used_at.isoformat() if form and form.used_at else None,
    }


@api_view(['GET'])
def id_card_student_list(request):
    institution_id = request.GET.get('institution_id')
    student_class = request.GET.get('student_class')
    div = request.GET.get('div')

    if not institution_id:
        return JsonResponse({'message': 'institution_id required'}, status=400)

    students = StudentData.objects.filter(institution_id=institution_id)
    if student_class:
        students = students.filter(student_class=student_class)
    if div:
        students = students.filter(div=div)

    forms = { (form.institution_id, form.admno): form for form in IDCardForm.objects.filter(institution_id=institution_id) }
    data = [_serialize_id_card(student, forms.get((student.institution_id, student.admno))) for student in students.order_by('student_class', 'div', 'student_name')]
    return JsonResponse(data, safe=False)


@api_view(['POST'])
def send_id_card_link(request):
    data = request.data
    institution_id = data.get('institution_id')
    admno = data.get('admno')

    if not institution_id or not admno:
        return JsonResponse({'message': 'institution_id and admno required'}, status=400)

    try:
        student = StudentData.objects.get(institution_id=institution_id, admno=admno)
    except StudentData.DoesNotExist:
        return JsonResponse({'message': 'Student not found'}, status=404)

    if not student.mobile:
        return JsonResponse({'message': 'Student mobile number is required to send WhatsApp link'}, status=400)

    form, created = IDCardForm.objects.get_or_create(
        institution_id=institution_id,
        admno=admno,
        defaults={'token': IDCardForm.generate_token()}
    )

    if not created:
        form.token = IDCardForm.generate_token()
        form.status = IDCardForm.STATUS_PENDING
        form.used_at = None
        form.save()

    link = _build_parent_link(form.token)
    message = (
        f"Dear Parent,\n\n"
        f"Please complete your child's ID Card details by clicking the link below:\n\n"
        f"{link}\n\n"
        f"All fields are required. The link is valid for one-time use only."
    )

    try:
        _send_whatsapp_message(student.mobile, message)
    except Exception as exc:
        return JsonResponse({'message': 'Failed to send WhatsApp message', 'error': str(exc)}, status=500)

    form.sent_at = now()
    form.status = IDCardForm.STATUS_PENDING
    form.save()

    return JsonResponse({'status': True, 'message': 'WhatsApp link sent', 'link': link})


@api_view(['POST'])
def bulk_send_id_card_links(request):
    data = request.data
    institution_id = data.get('institution_id')
    student_class = data.get('student_class')
    div = data.get('div')

    if not institution_id:
        return JsonResponse({'message': 'institution_id required'}, status=400)

    students = StudentData.objects.filter(institution_id=institution_id)
    if student_class:
        students = students.filter(student_class=student_class)
    if div:
        students = students.filter(div=div)

    results = []
    sent_count = 0
    for student in students:
        if not student.mobile:
            results.append({'admno': student.admno, 'status': 'skipped', 'reason': 'missing mobile'})
            continue
        form, _ = IDCardForm.objects.get_or_create(
            institution_id=institution_id,
            admno=student.admno,
            defaults={'token': IDCardForm.generate_token()}
        )
        form.token = IDCardForm.generate_token()
        form.status = IDCardForm.STATUS_PENDING
        form.used_at = None
        form.save()
        link = _build_parent_link(form.token)
        message = (
            f"Dear Parent,\n\n"
            f"Please complete your child's ID Card details by clicking the link below:\n\n"
            f"{link}\n\n"
            f"All fields are required. The link is valid for one-time use only."
        )
        try:
            _send_whatsapp_message(student.mobile, message)
            form.sent_at = now()
            form.save()
            sent_count += 1
            results.append({'admno': student.admno, 'status': 'sent'})
        except Exception as exc:
            results.append({'admno': student.admno, 'status': 'failed', 'reason': str(exc)})

    return JsonResponse({'status': True, 'sent_count': sent_count, 'results': results})


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def parent_link_info(request):
    token = request.GET.get('token')
    if not token:
        return JsonResponse({'message': 'token required'}, status=400)

    try:
        form = IDCardForm.objects.get(token=token)
    except IDCardForm.DoesNotExist:
        return JsonResponse({'message': 'Link not found or expired'}, status=404)

    if form.status != IDCardForm.STATUS_PENDING:
        return JsonResponse({'message': 'This link has already been used or is no longer valid'}, status=410)

    return JsonResponse({
        'institution_id': form.institution_id,
        'admno': form.admno,
        'student_name': form.student_name,
        'place': form.place,
        'district': form.district,
        'city': form.city,
        'state': form.state,
        'pin': form.pin,
        'phone': form.phone,
        'email': form.email,
        'father_name': form.father_name,
        'mother_name': form.mother_name,
        'dob': form.dob.isoformat() if form.dob else '',
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def submit_id_card_form(request):
    data = request.data
    token = data.get('token')
    if not token:
        return JsonResponse({'message': 'token required'}, status=400)

    try:
        form = IDCardForm.objects.get(token=token)
    except IDCardForm.DoesNotExist:
        return JsonResponse({'message': 'Link not found or expired'}, status=404)

    if form.status != IDCardForm.STATUS_PENDING:
        return JsonResponse({'message': 'This link has already been used'}, status=410)

    required_fields = ['student_name', 'place', 'district', 'city', 'state', 'pin', 'phone', 'email', 'father_name', 'mother_name', 'dob']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return JsonResponse({'message': f'Missing fields: {", ".join(missing)}'}, status=400)

    form.student_name = data.get('student_name')
    form.place = data.get('place')
    form.district = data.get('district')
    form.city = data.get('city')
    form.state = data.get('state')
    form.pin = data.get('pin')
    form.phone = data.get('phone')
    form.email = data.get('email')
    form.father_name = data.get('father_name')
    form.mother_name = data.get('mother_name')
    try:
        form.dob = datetime.fromisoformat(data.get('dob')).date()
    except ValueError:
        return JsonResponse({'message': 'Invalid date of birth format. Use YYYY-MM-DD.'}, status=400)

    form.status = IDCardForm.STATUS_USED
    form.used_at = now()
    form.save()

    return JsonResponse({'status': True, 'message': 'Details saved successfully'})


@api_view(['GET'])
def id_card_submission_detail(request):
    institution_id = request.GET.get('institution_id')
    admno = request.GET.get('admno')

    if not institution_id or not admno:
        return JsonResponse({'message': 'institution_id and admno required'}, status=400)

    try:
        form = IDCardForm.objects.get(institution_id=institution_id, admno=admno)
        return JsonResponse({
            'id': form.id,
            'institution_id': form.institution_id,
            'admno': form.admno,
            'status': form.status,
            'token': form.token,
            'student_name': form.student_name,
            'place': form.place,
            'district': form.district,
            'city': form.city,
            'state': form.state,
            'pin': form.pin,
            'phone': form.phone,
            'email': form.email,
            'father_name': form.father_name,
            'mother_name': form.mother_name,
            'dob': form.dob.isoformat() if form.dob else '',
            'sent_at': form.sent_at.isoformat() if form.sent_at else None,
            'used_at': form.used_at.isoformat() if form.used_at else None,
        })
    except IDCardForm.DoesNotExist:
        return JsonResponse({'message': 'No ID card submission found for this student'}, status=404)


@api_view(['PUT'])
def update_id_card_submission(request, pk):
    data = request.data
    try:
        form = IDCardForm.objects.get(pk=pk)
    except IDCardForm.DoesNotExist:
        return JsonResponse({'message': 'Submission not found'}, status=404)

    required_fields = ['student_name', 'place', 'district', 'city', 'state', 'pin', 'phone', 'email', 'father_name', 'mother_name', 'dob']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return JsonResponse({'message': f'Missing fields: {", ".join(missing)}'}, status=400)

    form.student_name = data.get('student_name')
    form.place = data.get('place')
    form.district = data.get('district')
    form.city = data.get('city')
    form.state = data.get('state')
    form.pin = data.get('pin')
    form.phone = data.get('phone')
    form.email = data.get('email')
    form.father_name = data.get('father_name')
    form.mother_name = data.get('mother_name')
    try:
        form.dob = datetime.fromisoformat(data.get('dob')).date()
    except ValueError:
        return JsonResponse({'message': 'Invalid date of birth format. Use YYYY-MM-DD.'}, status=400)

    form.save()
    return JsonResponse({'status': True, 'message': 'Submission updated successfully'})
