import json
import os
import re
import boto3
import io
import requests
from botocore.config import Config
from datetime import datetime
from django.http import JsonResponse, FileResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from xhtml2pdf import pisa

from student_data.models import StudentData
from add_administrators.models import SchoolInfo
from .models import IDCardForm


# ── Cloudflare R2 helpers ─────────────────────────────────────────────────────
def _get_r2_client():
    """Create and return Cloudflare R2 client with proper error handling."""
    try:
        # Get credentials from Django settings
        endpoint_url = getattr(settings, 'CLOUDFLARE_R2_BUCKET_ENDPOINT', '')
        access_key = getattr(settings, 'CLOUDFLARE_R2_ACCESS_KEY', '')
        secret_key = getattr(settings, 'CLOUDFLARE_R2_SECRET_KEY', '')
        
        if not all([endpoint_url, access_key, secret_key]):
            raise ValueError("Missing Cloudflare R2 credentials in settings")
        
        return boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
            region_name='auto',
        )
    except Exception as e:
        raise ValueError(f"Failed to create R2 client: {str(e)}")

R2_BUCKET = getattr(settings, 'CLOUDFLARE_R2_BUCKET', 'magnetschoolbackend')
R2_PUBLIC_URL = getattr(settings, 'CLOUDFLARE_R2_PUBLIC_URL', '').rstrip('/')


def _upload_photo_to_r2(file_obj, institution_id, admno):
    """Upload photo to Cloudflare R2 with enhanced error handling."""
    try:
        ext = os.path.splitext(file_obj.name)[1].lower() or '.jpg'
        content_type_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                            '.png': 'image/png', '.webp': 'image/webp'}
        content_type = content_type_map.get(ext, 'image/jpeg')
        object_key = f'id_card_photos/{institution_id}/{admno}{ext}'
        
        client = _get_r2_client()
        
        # Reset file pointer to beginning
        file_obj.seek(0)
        
        client.upload_fileobj(
            file_obj, R2_BUCKET, object_key,
            ExtraArgs={'ContentType': content_type, 'CacheControl': 'public, max-age=31536000'}
        )
        
        photo_url = f'{R2_PUBLIC_URL}/{object_key}'
        
        return photo_url, object_key
        
    except Exception as e:
        raise ValueError(f"Upload failed: {str(e)}")


def _delete_from_r2(key):
    if not key:
        return
    try:
        _get_r2_client().delete_object(Bucket=R2_BUCKET, Key=key)
    except Exception:
        pass


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
        'photo_url': form.photo_url if form else None,
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


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def lookup_by_phone(request):
    """Step 1: parent enters phone number → returns all matching students."""
    phone = request.data.get('phone', '').strip()
    if not phone:
        return JsonResponse({'message': 'Phone number is required.'}, status=400)

    digits = re.sub(r'\D', '', phone)
    last10 = digits[-10:] if len(digits) >= 10 else digits

    students = StudentData.objects.filter(mobile__endswith=last10)
    if not students.exists():
        return JsonResponse({'message': 'No student found with this phone number. Please check and try again.'}, status=404)

    results = []
    for student in students:
        form = IDCardForm.objects.filter(institution_id=student.institution_id, admno=student.admno).first()
        already_submitted = bool(form and form.status == IDCardForm.STATUS_USED)
        results.append({
            'institution_id': student.institution_id,
            'admno': student.admno,
            'student_name': student.student_name,
            'student_class': student.student_class,
            'div': student.div,
            'already_submitted': already_submitted,
            'form_id': form.id if form else None,
            'existing': {
                'student_name': form.student_name if form else '',
                'father_name':  form.father_name  if form else '',
                'mother_name':  form.mother_name  if form else '',
                'dob':          form.dob.isoformat() if form and form.dob else '',
                'phone':        form.phone        if form else '',
                'email':        form.email        if form else '',
                'place':        form.place        if form else '',
                'district':     form.district     if form else '',
                'city':         form.city         if form else '',
                'state':        form.state        if form else '',
                'pin':          form.pin          if form else '',
            } if form else None,
        })

    return JsonResponse({'found': True, 'students': results})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def submit_id_card_form_by_phone(request):
    """Submit or update ID card details looked up by phone (no token needed)."""
    data = request.data
    institution_id = data.get('institution_id')
    admno = data.get('admno')

    if not institution_id or not admno:
        return JsonResponse({'message': 'institution_id and admno are required.'}, status=400)

    required_fields = ['student_name', 'father_name', 'mother_name', 'dob', 'phone',
                       'email', 'place', 'district', 'city', 'state', 'pin']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return JsonResponse({'message': f'Missing fields: {", ".join(missing)}'}, status=400)

    form, _ = IDCardForm.objects.get_or_create(
        institution_id=institution_id,
        admno=admno,
        defaults={'token': IDCardForm.generate_token()}
    )

    form.student_name = data.get('student_name')
    form.father_name  = data.get('father_name')
    form.mother_name  = data.get('mother_name')
    form.phone        = data.get('phone')
    form.email        = data.get('email')
    form.place        = data.get('place')
    form.district     = data.get('district')
    form.city         = data.get('city')
    form.state        = data.get('state')
    form.pin          = data.get('pin')
    try:
        form.dob = datetime.fromisoformat(data.get('dob')).date()
    except (ValueError, TypeError):
        return JsonResponse({'message': 'Invalid date of birth format. Use YYYY-MM-DD.'}, status=400)

    form.status  = IDCardForm.STATUS_USED
    form.used_at = now()
    form.save()

    return JsonResponse({'status': True, 'message': 'Details saved successfully.'})


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_student_photo(request):
    """Upload student photo to Cloudflare R2."""
    try:
        institution_id = request.data.get('institution_id')
        admno = request.data.get('admno')
        photo = request.FILES.get('photo')

        if not institution_id or not admno:
            return JsonResponse({'message': 'institution_id and admno required'}, status=400)
        if not photo:
            return JsonResponse({'message': 'photo file required'}, status=400)
        if not photo.content_type.startswith('image/'):
            return JsonResponse({'message': 'Only image files are allowed'}, status=400)
        if photo.size > 5 * 1024 * 1024:
            return JsonResponse({'message': 'Photo must be under 5MB'}, status=400)

        form, created = IDCardForm.objects.get_or_create(
            institution_id=institution_id,
            admno=admno,
            defaults={'token': IDCardForm.generate_token()}
        )

        # Delete old photo
        if form.photo_key:
            _delete_from_r2(form.photo_key)

        try:
            url, key = _upload_photo_to_r2(photo, institution_id, admno)
            form.photo_url = url
            form.photo_key = key
            form.save()
            
            return JsonResponse({'status': True, 'photo_url': url})
            
        except Exception as upload_error:
            return JsonResponse({'message': str(upload_error)}, status=500)
            
    except Exception as e:
        return JsonResponse({'message': f'Server error: {str(e)}'}, status=500)


@api_view(['GET'])
def id_card_school_info(request):
    """Get school info for id card display."""
    institution_id = request.GET.get('institution_id')
    if not institution_id:
        return JsonResponse({'message': 'institution_id required'}, status=400)
    try:
        info = SchoolInfo.objects.get(institution_id=institution_id)
        return JsonResponse({
            'school_name': info.school_name,
            'address': info.address,
            'place': info.place,
            'pincode': info.pincode,
            'phone': info.phone,
            'email': info.email,
            'logo_url': info.logo_url,
        })
    except SchoolInfo.DoesNotExist:
        return JsonResponse({}, status=200)


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


# ── PDF GENERATION ENDPOINT (Backend using WeasyPrint) ────────────────────────

def _fetch_image_as_base64(image_url):
    """
    Fetch image from URL (including Cloudflare R2) and convert to base64.
    This solves CORS issues by downloading on the server side.
    """
    if not image_url:
        return None
    
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            import base64
            b64 = base64.b64encode(response.content).decode('utf-8')
            content_type = response.headers.get('content-type', 'image/jpeg')
            return f"data:{content_type};base64,{b64}"
        else:
            print(f"Failed to fetch image: {image_url} (status {response.status_code})")
            return None
    except Exception as e:
        print(f"Error fetching image {image_url}: {str(e)}")
        return None


@api_view(['POST'])
def generate_id_card_pdf(request):
    """Generate ID card PDF using xhtml2pdf on the server."""
    try:
        data = request.data
        student = data.get('student', {})
        school = data.get('school', {})
        details = data.get('details', {})
        
        # Fetch and convert images to base64
        student_photo_b64 = _fetch_image_as_base64(student.get('photo_url'))
        school_logo_b64 = _fetch_image_as_base64(school.get('logo_url'))
        
        # Build address
        full_address = ', '.join(filter(None, [
            details.get('place'),
            details.get('district'),
            details.get('city'),
            details.get('state'),
            details.get('pin'),
        ]))
        
        # Prepare context
        context = {
            'student_name': (student.get('student_name') or '').upper(),
            'student_class': student.get('student_class', ''),
            'div': student.get('div', ''),
            'admno': student.get('admno', ''),
            'mobile': student.get('mobile', ''),
            'school_name': school.get('school_name', ''),
            'school_address': school.get('address', ''),
            'school_place': school.get('place', ''),
            'school_phone': school.get('phone', ''),
            'school_email': school.get('email', ''),
            'full_address': full_address or 'Address not provided',
            'student_photo': student_photo_b64,
            'school_logo': school_logo_b64,
        }
        
        # Render HTML template
        html_content = render_to_string('id_card_template.html', context)
        
        # Generate PDF with xhtml2pdf
        pdf_file = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        
        if pisa_status.err:
            raise Exception(f'xhtml2pdf error: {pisa_status.err}')
        
        pdf_file.seek(0)
        
        # Return PDF as file download
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ID_Card_{student.get("admno", "student")}.pdf"'
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': False, 'message': f'PDF generation failed: {str(e)}'}, status=500)


@api_view(['POST'])
def generate_bulk_id_card_pdf(request):
    """
    Generate PDF for multiple students.
    
    Request body:
    {
        "institution_id": "inst_123",
        "students": [
            { "student": {...}, "details": {...} },
            { "student": {...}, "details": {...} }
        ],
        "school": {...}
    }
    """
    try:
        data = request.data
        institution_id = data.get('institution_id')
        students_data = data.get('students', [])
        school = data.get('school', {})
        
        if not students_data:
            return JsonResponse({'message': 'No students provided'}, status=400)
        
        # Fetch school logo once
        school_logo_b64 = _fetch_image_as_base64(school.get('logo_url'))
        
        # Generate HTML for all students
        all_html = '<html><head><style>page { page-break-after: always; }</style></head><body>'
        
        for idx, student_info in enumerate(students_data):
            student = student_info.get('student', {})
            details = student_info.get('details', {})
            
            # Fetch student photo
            student_photo_b64 = _fetch_image_as_base64(student.get('photo_url'))
            
            # Build address
            full_address = ', '.join(filter(None, [
                details.get('place'),
                details.get('district'),
                details.get('city'),
                details.get('state'),
                details.get('pin'),
            ]))
            
            context = {
                'student_name': (student.get('student_name') or '').upper(),
                'student_class': student.get('student_class', ''),
                'div': student.get('div', ''),
                'admno': student.get('admno', ''),
                'mobile': student.get('mobile', ''),
                'school_name': school.get('school_name', ''),
                'school_address': school.get('address', ''),
                'school_place': school.get('place', ''),
                'school_phone': school.get('phone', ''),
                'school_email': school.get('email', ''),
                'full_address': full_address or 'Address not provided',
                'student_photo': student_photo_b64,
                'school_logo': school_logo_b64,
            }
            
            # Render individual card
            card_html = render_to_string('id_card_template.html', context)
            all_html += f'<div style="page-break-after: always;">{card_html}</div>'
        
        all_html += '</body></html>'
        
        # Generate bulk PDF with xhtml2pdf
        pdf_file = io.BytesIO()
        pisa_status = pisa.CreatePDF(all_html, dest=pdf_file)
        
        if pisa_status.err:
            raise Exception(f'xhtml2pdf error: {pisa_status.err}')
        
        pdf_file.seek(0)
        
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="ID_Cards_Bulk.pdf"'
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': False, 'message': f'Bulk PDF generation failed: {str(e)}'}, status=500)
