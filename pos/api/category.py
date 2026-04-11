from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from pos.models import Category
from pos.serializers import CategorySerializer
from pos.services import delete_category_image
from django.core.paginator import Paginator

class CategoryApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            try:
                category = Category.objects.get(pk=pk, is_deleted=False)
                return Response(CategorySerializer(category, context={'request': request}).data)
            except Category.DoesNotExist:
                return Response({"message": "Categoría no encontrada", "code": 404}, status=404)

        search = request.GET.get('search', '')
        page_number = request.GET.get('page', 1)
        
        categories_query = Category.objects.filter(
            is_deleted=False,
            title__icontains=search
        ).order_by('-id')
        
        paginator = Paginator(categories_query, 5)  # paginate(5)
        page_obj = paginator.get_page(page_number)

        return Response({
            "total": paginator.count,
            "paginate": 5,
            "categories": CategorySerializer(page_obj, many=True, context={'request': request}).data
        })

    def post(self, request):
        title = request.data.get('title')
        if not title:
            return Response({"code": 400, "message": "El título es obligatorio"}, status=400)
        
        if Category.objects.filter(title=title, is_deleted=False).exists():
            return Response({
                "code": 405,
                "message": "La categoría ya existe, intente con otro nombre"
            })

        category = Category.objects.create(
            title=title,
            icon_name=request.data.get("icon_name", "LayoutGrid"),
            is_active=self._parse_bool(request.data.get("is_active", True)),
        )

        if request.FILES.get("image"):
            category.imagen = request.FILES.get("image")
            category.save()

        return Response({
            "code": 200,
            "message": "Categoría creada correctamente",
            "categorie": CategorySerializer(category, context={'request': request}).data
        })

    def put(self, request, pk):
        try:
            category = Category.objects.get(pk=pk, is_deleted=False)
        except Category.DoesNotExist:
            return Response({"message": "Categoría no encontrada", "code": 404}, status=404)

        title = request.data.get('title')
        if title and Category.objects.filter(title=title, is_deleted=False).exclude(pk=pk).exists():
            return Response({
                "code": 405,
                "message": "La categoría ya existe, intente con otro nombre"
            })

        if "title" in request.data:
            category.title = request.data.get("title")
        if "icon_name" in request.data:
            category.icon_name = request.data.get("icon_name")
        if "is_active" in request.data:
            category.is_active = self._parse_bool(request.data.get("is_active"))

        if request.FILES.get("image"):
            delete_category_image(category)
            category.imagen = request.FILES.get("image")

        category.save()

        return Response({
            "code": 200,
            "message": "Categoría actualizada correctamente",
            "categorie": CategorySerializer(category, context={'request': request}).data
        })

    def patch(self, request, pk):
        """PATCH para actualizaciones parciales (ej. toggle is_active)."""
        return self.put(request, pk)

    def delete(self, request, pk):
        try:
            category = Category.objects.get(pk=pk, is_deleted=False)
            delete_category_image(category)
            category.is_deleted = True
            category.save()
            return Response({
                "code": 200,
                "message": "Categoría eliminada correctamente"
            })
        except Category.DoesNotExist:
            return Response({"message": "Categoría no encontrada", "code": 404}, status=404)

    @staticmethod
    def _parse_bool(value):
        """Convierte string 'True'/'False' de FormData a boolean Python."""
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)