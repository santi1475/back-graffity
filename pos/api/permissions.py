from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Permission

class PermissionApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        models_pos = ['user', 'product', 'category', 'brand', 'company']
        permissions = Permission.objects.filter(
            content_type__model__in=models_pos
        ).order_by('content_type__model')

        data = [{
            "id": p.id,
            "name": p.name,      
            "codename": p.codename, 
            "module": p.content_type.model 
        } for p in permissions]

        return Response(data)
