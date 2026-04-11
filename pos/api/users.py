from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import Q
from pos.models import User
from pos.serializers import UserSerializer

class UserApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            try:
                user = User.objects.get(pk=pk, is_deleted=False)
                return Response(UserSerializer(user).data)
            except User.DoesNotExist:
                return Response({"code": 404, "message": "Usuario no encontrado"}, status=404)

        # INDEX: Búsqueda y Paginación
        search = request.GET.get("search")
        # Siempre filtramos los que no están eliminados (Soft Delete)
        query = User.objects.filter(is_deleted=False)

        if search:
            query = query.filter(
                Q(name__icontains=search) |
                Q(surname__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(n_document__icontains=search)
            )

        # Paginación de 25 como en tu userController.php [cite: 5]
        paginator = Paginator(query.order_by("-id"), 25)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        roles = Group.objects.all()

        return Response({
            "total": paginator.count,
            "paginate": 25,
            "users": UserSerializer(page_obj, many=True).data,
            "roles": [{"id": r.id, "name": r.name} for r in roles]
        })

    def post(self, request):
        email = request.data.get("email")
        if User.objects.filter(email=email).exists():
            return Response({
                "code": 405, 
                "message": f"El correo {email} ya se encuentra registrado"
            })

        # Usamos tu UserManager.create_user
        user = User.objects.create_user(
            email=email,
            password=request.data.get("password"),
            name=request.data.get("name"),
            surname=request.data.get("surname"),
            phone=request.data.get("phone"),
            type_document=request.data.get("type_document"),
            n_document=request.data.get("n_document"),
            gender=request.data.get("gender"),
            is_active=request.data.get("is_active", True)
        )

        if request.FILES.get("avatar"):
            user.avatar = request.FILES.get("avatar")

        role_id = request.data.get("role_id")
        if role_id and str(role_id) != "0":
            user.role = Group.objects.get(pk=int(role_id))
        
        user.save()

        return Response({
            "code": 200,
            "message": "Usuario creado correctamente",
            "user": UserSerializer(user).data
        })

    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk, is_deleted=False)
        except User.DoesNotExist:
            return Response({"code": 404, "message": "Usuario no encontrado"})

        email = request.data.get("email")
        if User.objects.filter(email=email).exclude(pk=pk).exists():
            return Response({"code": 405, "message": "El correo ya existe"})

        if "name" in request.data: user.name = request.data.get("name")
        if "surname" in request.data: user.surname = request.data.get("surname")
        
        user.email = email
        
        if "phone" in request.data: user.phone = request.data.get("phone")
        if "type_document" in request.data: user.type_document = request.data.get("type_document")
        if "n_document" in request.data: user.n_document = request.data.get("n_document")

        if "gender" in request.data:
            gender_val = request.data.get("gender")
            user.gender = int(gender_val) if gender_val else None

        if "is_active" in request.data:
            active_val = request.data.get("is_active")
            if isinstance(active_val, str):
                user.is_active = active_val.lower() == "true"
            else:
                user.is_active = bool(active_val)

        if request.data.get("password"):
            user.set_password(request.data.get("password"))

        if request.FILES.get("avatar"):
            # Limpieza manual del avatar anterior si existe
            if user.avatar:
                user.avatar.delete(save=False)
            user.avatar = request.FILES.get("avatar")

        role_id = request.data.get("role_id")
        if role_id and str(role_id) != "0":
            user.role = Group.objects.get(pk=int(role_id))

        user.save()
        return Response({
            "code": 200,
            "message": "Usuario actualizado correctamente",
            "user": UserSerializer(user).data
        })

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.is_deleted = True
            user.save()
            return Response({
                "code": 200,
                "message": "Usuario eliminado correctamente"
            })
        except User.DoesNotExist:
            return Response({"code": 404, "message": "Usuario no encontrado"})
