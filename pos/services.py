import os
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.storage import default_storage
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Product, Category, Brand
from django.conf import settings


def auth_login(*, email: str, password: str) -> dict:
    """
    Autentica un usuario por email y password.
    Retorna un dict con access_token, token_type, expires_in y datos del usuario.
    Levanta ValidationError si las credenciales son inválidas.
    """
    user = authenticate(email=email, password=password)

    if user is None:
        raise ValidationError("Credenciales inválidas.")

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    # Calcular expires_in en segundos desde la configuración
    lifetime = settings.SIMPLE_JWT.get(
        'ACCESS_TOKEN_LIFETIME',
    )
    expires_in = int(lifetime.total_seconds())

    # Construir datos del rol (compatible con contrato Laravel)
    role_data = None
    if user.role is not None:
        permissions = list(
            user.role.permissions.values_list('codename', flat=True)
        )
        role_data = {
            "id": user.role.id,
            "name": user.role.name,
            "permissions": permissions,
        }

    # Construir avatar URL
    avatar_url = None
    if user.avatar and hasattr(user.avatar, 'url'):
        avatar_url = user.avatar.url

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user.id,
            "name": user.name,
            "surname": user.surname,
            "email": user.email,
            "avatar": avatar_url,
            "role": role_data,
        },
    }

def delete_brand_image(brand):
    if brand.image and hasattr(brand.image, 'path'):
        if os.path.exists(brand.image.path):
            os.remove(brand.image.path)
            
def delete_category_image(category):
    if category.image and hasattr(category.image, 'path'):
        if os.path.exists(category.image.path):
            os.remove(category.image.path)
            
def _generate_sku(category: Category, brand: Brand, title: str, product_id: int) -> str:
    brand_prefix = brand.name[:3].upper() if brand and brand.name else 'GEN'
    category_prefix = category.title[:3].upper() if category and category.title else 'VAR'
    title_prefix = title.replace(" ", "")[:4].upper() if title else 'PROD'
    
    return f"{brand_prefix}-{title_prefix}-{product_id}-{category_prefix}"

def product_create(*, data: dict) -> Product:
    # Sanitizar data: Extraer el primer elemento si los valores llegan como listas
    # Esto ocurre a menudo cuando se recibe 'multipart/form-data'
    sanitized_data = {}
    
    # Manejar caso de QueryDict de Django/DRF
    raw_data = data.dict() if hasattr(data, 'dict') else data
    
    for key, value in raw_data.items():
        if isinstance(value, list) and len(value) > 0:
            sanitized_data[key] = value[0]
        else:
            sanitized_data[key] = value

    sku = sanitized_data.get('sku')
    
    # Limpiar y castear IDs explícitamente para evitar problemas relacionales
    category_id = sanitized_data.get('category_id')
    brand_id = sanitized_data.get('brand_id')

    # Convertir a entero si es string o evitar fallo si llega None / vacío
    if category_id and str(category_id).isdigit():
        category_id = int(category_id)
    else:
        category_id = None
        
    if brand_id and str(brand_id).isdigit():
        brand_id = int(brand_id)
    else:
        brand_id = None

    # Remover campos que no deben insertarse en la creación o podrían causar conflictos
    sanitized_data.pop('id', None)
    sanitized_data.pop('sku', None) # Se autogenerará siempre según nueva regla
    
    # Asignar los IDs casteados a la data limpia
    if 'category_id' in sanitized_data:
        sanitized_data['category_id'] = category_id
    if 'brand_id' in sanitized_data:
        sanitized_data['brand_id'] = brand_id
        
    product = Product.objects.create(**sanitized_data)
    
    # Generar SKU basado en reglas (utiliza el ID de PostgreSQL ya asignado)
    category = Category.objects.filter(id=category_id).first() if category_id else None
    brand = Brand.objects.filter(id=brand_id).first() if brand_id else None
    sku_generado = _generate_sku(category, brand, product.title, product.id)
    
    # Asegurar unicidad (aunque la regla incluye ID que suele ser único, por si acaso)
    if Product.objects.filter(sku=sku_generado).exclude(id=product.id).exists():
        raise ValidationError("El SKU autogenerado del producto ya existe (colisión).")
        
    product.sku = sku_generado
    product.save(update_fields=['sku'])
    
    return product
def product_register(*, data: dict) -> Product:
    """Create a new product via API.
    Generates SKU if not provided, validates uniqueness, and returns the created Product.
    """
    # Reuse existing product_create logic which handles SKU generation and validation
    return product_create(data=data)

def product_update(*, product: Product, data: dict) -> Product:
    # Sanitizar data: Extraer el primer elemento si los valores llegan como listas
    sanitized_data = {}
    raw_data = data.dict() if hasattr(data, 'dict') else data
    
    for key, value in raw_data.items():
        if isinstance(value, list) and len(value) > 0:
            sanitized_data[key] = value[0]
        else:
            sanitized_data[key] = value

    # Remover campos protegidos
    sanitized_data.pop('id', None)
    sanitized_data.pop('sku', None)
    
    category_id = sanitized_data.pop('category_id', None)
    brand_id = sanitized_data.pop('brand_id', None)
    
    # Casteo seguro
    if category_id is not None:
        if str(category_id).isdigit():
            product.category_id = int(category_id)
        else:
            product.category_id = None
            
    if brand_id is not None:
        if str(brand_id).isdigit():
            product.brand_id = int(brand_id)
        else:
            product.brand_id = None

    # Actualizar campos directamente
    for field, value in sanitized_data.items():
        # Evitar sobreescribir con blancos valores que no deben (por ej. imagen si no se envía)
        # Solo actualizamos el campo de image si explicitly viene en el data y es un file/str
        if field == 'image' and not value:
            continue
        if hasattr(product, field):
            setattr(product, field, value)
            
    product.save()
    
    # Recalcular SKU basado en las mismas reglas (por si cambió marca, categoría o título)
    category = Category.objects.filter(id=product.category_id).first() if product.category_id else None
    brand = Brand.objects.filter(id=product.brand_id).first() if product.brand_id else None
    sku_generado = _generate_sku(category, brand, product.title, product.id)
    
    if product.sku != sku_generado:
        if not Product.objects.filter(sku=sku_generado).exclude(id=product.id).exists():
            product.sku = sku_generado
            product.save(update_fields=['sku'])
            
    return product

def product_soft_delete(*, product: Product):

    product.is_deleted = True
    product.save(update_fields=['is_deleted'])

def process_product_scan(*, barcode: str, channel_uuid: str):
    """
    Equivalente a App\\Events\\ProductScanned.
    Utiliza Django Channels para emitir al canal: scan_{channel_uuid}
    """
    from django.db.models import Q
    product = Product.objects.filter(Q(sku=barcode) | Q(barcode=barcode), is_deleted=False).first()
    
    is_new = product is None
    
    # Emitir via Websockets (Django Channels)
    channel_layer = get_channel_layer()
    if channel_layer:
        # Importación local para evitar dependencias circulares
        from .serializers import ProductSerializer 
        product_data = ProductSerializer(product).data if product else None
        
        async_to_sync(channel_layer.group_send)(
            f"scan_{channel_uuid}",
            {
                "type": "product.scanned", # El handler en tu consumer
                "barcode": barcode,
                "productData": product_data,
                "is_new": is_new
            }
        )
    return product