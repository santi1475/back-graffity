from django.core.paginator import Paginator, EmptyPage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from pos.models import Product, Category, Brand
from pos.serializers import ProductSerializer
from pos.selectors import product_list
from pos.services import product_register, product_soft_delete, process_product_scan

class ProductApi(APIView):
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        qs = product_list(
            search=request.GET.get('search'),
            category_id=request.GET.get('categorie_id'),
            brand_id=request.GET.get('brand_id'),
            state=request.GET.get('state'),
            unidad_medida=request.GET.get('unidad_medida')
        )
        paginator = Paginator(qs, 25)  # default page size
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            return Response({"detail": "Page out of range"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(page_obj.object_list, many=True)
        return Response({
            "total": paginator.count,
            "page": page,
            "page_size": paginator.per_page,
            "products": serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            product = product_register(data=request.data)
            serializer = ProductSerializer(product)
            return Response({
                "code": 200,
                "message": "Producto creado exitosamente.",
                "product": serializer.data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"code": 405, "message": str(e.message)}, status=status.HTTP_400_BAD_REQUEST)

class ProductDetailApi(APIView):
    def delete(self, request, pk):
        product = Product.objects.filter(pk=pk, is_deleted=False).first()
        if not product:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        product_soft_delete(product=product)
        return Response({
            "code": 200,
            "message": "Producto eliminado exitosamente."
        }, status=status.HTTP_200_OK)

class ProductConfigApi(APIView):
    def get(self, request):
        categories = Category.objects.filter(is_deleted=False, state=1).values('id', 'title')
        brands = Brand.objects.filter(is_deleted=False, state=1).values('id', 'name')
        latest_product = Product.objects.order_by('-id').first()
        next_id = (latest_product.id + 1) if latest_product else 1
        
        return Response({
            "next_product_id": next_id,
            "categories": list(categories),
            "brands": list(brands)
        })

class ProductScanApi(APIView):
    def post(self, request):
        barcode = request.data.get('barcode')
        channel_uuid = request.data.get('channel_uuid')
        
        if not barcode or not channel_uuid:
            return Response({"error": "barcode y channel_uuid son requeridos"}, status=status.HTTP_400_BAD_REQUEST)
            
        product = process_product_scan(barcode=barcode, channel_uuid=channel_uuid)
        
        return Response({
            'message': 'Código enviado correctamente',
            'product_found': bool(product),
            'product_name': product.title if product else None
        }, status=status.HTTP_200_OK)