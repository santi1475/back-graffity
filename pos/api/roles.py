from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from pos.serializers import RoleSerializer

class RoleApi(APIView):
    permission_classes = [IsAuthenticated] # Protege la ruta

    def get(self, request, pk=None):
        # Si envían un ID, devolvemos uno (Show)
        if pk:
            try:
                role = Group.objects.get(pk=pk)
                return Response(RoleSerializer(role).data)
            except Group.DoesNotExist:
                return Response({"message": "Rol no encontrado", "code": 404}, status=404)

        # INDEX: Paginación y búsqueda
        search = request.GET.get('search', '')
        page_number = request.GET.get('page', 1)
        
        # Filtramos como en Laravel: where("name", "like", "%$search%")
        roles_query = Group.objects.filter(name__icontains=search).order_by('-id')
        
        paginator = Paginator(roles_query, 5) # paginate(5)
        page_obj = paginator.get_page(page_number)

        return Response({
            "total": paginator.count,
            "paginate": 5,
            "roles": RoleSerializer(page_obj, many=True).data
        })

    def post(self, request):
        # STORE
        name = request.data.get('name')
        permissions_list = request.data.get('permissions', []) # Array de IDs o codenames

        if Group.objects.filter(name=name).exists():
            return Response({
                "code": 405,
                "message": "El rol ya existe, intente con otro nombre"
            })

        role = Group.objects.create(name=name)
        
        # Asignar permisos: Equivale a givePermissionTo()
        if permissions_list:
            # Asumiendo que el front envía IDs de permisos
            role.permissions.set(permissions_list) 

        return Response({
            "code": 200,
            "message": "Rol creado correctamente",
            "role": RoleSerializer(role).data
        })

    def put(self, request, pk):
        # UPDATE
        try:
            role = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response({"message": "Rol no encontrado", "code": 404})

        name = request.data.get('name')
        permissions_list = request.data.get('permissions', [])

        # Validar si existe otro rol con ese nombre (excepto él mismo)
        if Group.objects.filter(name=name).exclude(pk=pk).exists():
            return Response({
                "code": 405,
                "message": "El rol ya existe, intente con otro nombre"
            })

        role.name = name
        role.save()

        # Sincronizar permisos: Django .set() elimina los viejos y pone los nuevos (Igual a syncPermissions)
        role.permissions.set(permissions_list)

        return Response({
            "code": 200,
            "message": "Rol actualizado correctamente",
            "role": RoleSerializer(role).data
        })

    def delete(self, request, pk):
        # DESTROY
        try:
            role = Group.objects.get(pk=pk)
            role.delete()
            return Response({
                "code": 200,
                "message": "Rol eliminado correctamente"
            })
        except Group.DoesNotExist:
            return Response({"message": "Rol no encontrado", "code": 404})
