from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Q
from pos.models import Brand
from pos.serializers import BrandSerializer
from pos.services import delete_brand_image

class BrandApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            try:
                brand = Brand.objects.get(pk=pk, is_deleted=False)
                return Response(BrandSerializer(brand).data)
            except Brand.DoesNotExist:
                return Response({"code": 404, "message": "Marca no encontrada"}, status=404)

        search = request.GET.get("search")
        query = Brand.objects.filter(is_deleted=False)

        if search:
            query = query.filter(Q(name__icontains=search))

        paginator = Paginator(query.order_by("-id"), 25)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        return Response({
            "total": paginator.count,
            "paginate": 25,
            "brands": BrandSerializer(page_obj, many=True).data
        })

    def post(self, request):
        name = request.data.get("name")
        if not name:
            return Response({"code": 400, "message": "El nombre es obligatorio"}, status=400)

        if Brand.objects.filter(name=name, is_deleted=False).exists():
            return Response({
                "code": 405,
                "message": f"La marca '{name}' ya se encuentra registrada"
            })

        brand = Brand.objects.create(
            name=name,
            icon_name=request.data.get("icon_name", "Tag"),
            is_active=self._parse_bool(request.data.get("is_active", True)),
        )

        if request.FILES.get("image"):
            brand.image = request.FILES.get("image")
            brand.save()

        return Response({
            "code": 200,
            "message": "Marca creada correctamente",
            "brand": BrandSerializer(brand).data
        })

    def put(self, request, pk):
        try:
            brand = Brand.objects.get(pk=pk, is_deleted=False)
        except Brand.DoesNotExist:
            return Response({"code": 404, "message": "Marca no encontrada"}, status=404)

        if "name" in request.data:
            brand.name = request.data.get("name")
        if "icon_name" in request.data:
            brand.icon_name = request.data.get("icon_name")
        if "is_active" in request.data:
            brand.is_active = self._parse_bool(request.data.get("is_active"))

        if request.FILES.get("image"):
            delete_brand_image(brand)
            brand.image = request.FILES.get("image")

        brand.save()
        return Response({
            "code": 200,
            "message": "Marca actualizada correctamente",
            "brand": BrandSerializer(brand).data
        })

    def patch(self, request, pk):
        """PATCH para actualizaciones parciales (ej. toggle is_active)."""
        return self.put(request, pk)

    def delete(self, request, pk):
        try:
            brand = Brand.objects.get(pk=pk, is_deleted=False)
            delete_brand_image(brand)
            brand.is_deleted = True
            brand.save()
            return Response({
                "code": 200,
                "message": "Marca eliminada correctamente"
            })
        except Brand.DoesNotExist:
            return Response({"code": 404, "message": "Marca no encontrada"}, status=404)

    @staticmethod
    def _parse_bool(value):
        """Convierte string 'True'/'False' de FormData a boolean Python."""
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)