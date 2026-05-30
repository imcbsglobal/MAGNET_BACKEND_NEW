import os
import uuid
import boto3
from botocore.config import Config
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.forms.models import model_to_dict
from django.core.exceptions import MultipleObjectsReturned
from .models import AdministratorProfile, SchoolInfo


# ── Cloudflare R2 client (S3-compatible) ─────────────────────────────────────

def _get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv('CLOUDFLARE_R2_BUCKET_ENDPOINT'),
        aws_access_key_id=os.getenv('CLOUDFLARE_R2_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('CLOUDFLARE_R2_SECRET_KEY'),
        config=Config(signature_version='s3v4'),
        region_name='auto',
    )

R2_BUCKET = os.getenv('CLOUDFLARE_R2_BUCKET', 'magnetschoolbackend')
R2_PUBLIC_URL = os.getenv('CLOUDFLARE_R2_PUBLIC_URL', '').rstrip('/')


def _upload_logo_to_r2(file_obj, institution_id):
    """
    Upload a logo file to Cloudflare R2.
    Returns the public URL of the uploaded file.
    """
    ext = os.path.splitext(file_obj.name)[1].lower() or '.png'
    object_key = f'school_logos/{institution_id}/logo{ext}'

    content_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
    }
    content_type = content_type_map.get(ext, 'image/png')

    client = _get_r2_client()
    client.upload_fileobj(
        file_obj,
        R2_BUCKET,
        object_key,
        ExtraArgs={
            'ContentType': content_type,
            'CacheControl': 'public, max-age=31536000',
        }
    )

    # Return the public URL via R2 public bucket URL
    public_url = f'{R2_PUBLIC_URL}/{object_key}'
    return public_url, object_key


def _delete_logo_from_r2(object_key):
    """Delete an existing logo from R2 by its object key."""
    if not object_key:
        return
    try:
        client = _get_r2_client()
        client.delete_object(Bucket=R2_BUCKET, Key=object_key)
    except Exception:
        pass  # Non-critical — old file cleanup failure shouldn't block save


# ── Administrator CRUD ────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def administrator_list_create(request):
    if request.method == 'GET':
        administrators = AdministratorProfile.objects.all().order_by('-created_at')
        data = [model_to_dict(admin) for admin in administrators]
        return Response(data)

    elif request.method == 'POST':
        data = request.data
        try:
            administrator = AdministratorProfile.objects.create(
                school_name=data.get('school_name'),
                address=data.get('address'),
                city=data.get('city'),
                district=data.get('district'),
                pincode=data.get('pincode'),
                state=data.get('state'),
                email=data.get('email'),
                phone_number=data.get('phone_number'),
                institution_id=data.get('institution_id'),
                username=data.get('username'),
                password=data.get('password'),
            )
            return Response(model_to_dict(administrator), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def administrator_detail(request, pk):
    try:
        administrator = AdministratorProfile.objects.get(pk=pk)
    except AdministratorProfile.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(model_to_dict(administrator))

    elif request.method == 'PUT':
        data = request.data
        for field, value in data.items():
            setattr(administrator, field, value)
        administrator.save()
        return Response(model_to_dict(administrator))

    elif request.method == 'DELETE':
        administrator.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── School Info ───────────────────────────────────────────────────────────────

def _school_info_dict(info):
    return {
        'id': info.id,
        'institution_id': info.institution_id,
        'school_name': info.school_name,
        'address': info.address,
        'place': info.place,
        'pincode': info.pincode,
        'phone': info.phone,
        'email': info.email,
        'logo_url': info.logo_url,
        'updated_at': info.updated_at.isoformat(),
    }


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def school_info_get(request):
    """
    GET /api/school-info/?institution_id=XXX
    Returns the school info for the given institution.
    """
    institution_id = request.query_params.get('institution_id')
    if not institution_id:
        return Response({'error': 'institution_id required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        info = SchoolInfo.objects.get(institution_id=institution_id)
        return Response(_school_info_dict(info))
    except SchoolInfo.DoesNotExist:
        return Response({}, status=status.HTTP_200_OK)
    except MultipleObjectsReturned:
        # If there are duplicates (shouldn't happen), keep the most recently updated
        infos = SchoolInfo.objects.filter(institution_id=institution_id).order_by('-updated_at')
        primary = infos.first()
        # Remove duplicate records to enforce one-record-per-institution
        try:
            infos.exclude(pk=primary.pk).delete()
        except Exception:
            pass
        return Response(_school_info_dict(primary))


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def school_info_save(request):
    """
    POST /api/school-info/save/
    Creates or updates school info for the institution.
    Logo is uploaded to Cloudflare R2.
    """
    institution_id = request.data.get('institution_id')
    if not institution_id:
        return Response({'error': 'institution_id required'}, status=status.HTTP_400_BAD_REQUEST)

    school_name = request.data.get('school_name', '')
    address     = request.data.get('address', '')
    place       = request.data.get('place', '')
    pincode     = request.data.get('pincode', '')
    phone       = request.data.get('phone', '')
    email       = request.data.get('email', '')
    logo_file   = request.FILES.get('logo')

    # Get or create the record. If duplicates exist, consolidate them.
    try:
        info, _ = SchoolInfo.objects.get_or_create(
            institution_id=institution_id,
            defaults={
                'school_name': school_name,
                'address': address,
                'place': place,
                'pincode': pincode,
                'phone': phone,
                'email': email,
            }
        )
    except MultipleObjectsReturned:
        infos = SchoolInfo.objects.filter(institution_id=institution_id).order_by('-updated_at')
        info = infos.first()
        try:
            infos.exclude(pk=info.pk).delete()
        except Exception:
            pass

    # Update text fields
    info.school_name = school_name
    info.address     = address
    info.place       = place
    info.pincode     = pincode
    info.phone       = phone
    info.email       = email

    # Upload logo to Cloudflare R2 if a new file was provided
    if logo_file:
        try:
            # Delete old logo from R2 first
            if info.logo_public_id:
                _delete_logo_from_r2(info.logo_public_id)

            public_url, object_key = _upload_logo_to_r2(logo_file, institution_id)
            info.logo_url       = public_url
            info.logo_public_id = object_key
        except Exception as e:
            return Response(
                {'error': f'Logo upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    info.save()
    return Response(_school_info_dict(info), status=status.HTTP_200_OK)
