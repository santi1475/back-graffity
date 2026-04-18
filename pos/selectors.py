from django.db.models import QuerySet
from .models import Product, Category, Brand

def product_list(*, search=None, category_id=None, brand_id=None, state=None, unidad_medida=None) -> QuerySet[Product]:
    qs = Product.objects.filter(is_deleted=False).select_related('category', 'brand')
    
    if search:
        qs = qs.filter(title__icontains=search)
    if category_id:
        qs = qs.filter(category_id=category_id)
    if brand_id:
        qs = qs.filter(brand_id=brand_id)
    if state is not None:
        qs = qs.filter(state=state)
    if unidad_medida:
        qs = qs.filter(unidad_medida=unidad_medida)
        
    return qs.order_by('-id')

def category_list(*, search=None) -> QuerySet[Category]:
    qs = Category.objects.filter(is_deleted=False)
    if search:
        qs = qs.filter(title__icontains=search)
    return qs.order_by('-id')

def brand_list(*, search=None) -> QuerySet[Brand]:
    qs = Brand.objects.filter(is_deleted=False)
    if search:
        qs = qs.filter(name__icontains=search)
    return qs.order_by('-id')