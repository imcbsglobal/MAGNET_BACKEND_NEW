from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AdministratorProfile
from django.forms.models import model_to_dict

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
