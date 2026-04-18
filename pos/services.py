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
            
def _generate_sku(category: Category, brand: Brand) -> str:
    brand_prefix = brand.name[:3].upper() if brand else 'GEN'
    category_prefix = category.title[:3].upper() if category else 'VAR'
    
    category_count = Product.objects.filter(category=category, is_deleted=False).count()
    next_number = category_count + 1
    correlative = str(next_number).zfill(5)
    
    return f"{brand_prefix}-{category_prefix}-{correlative}"

def product_create(*, data: dict) -> Product:
    sku = data.get('sku')
    category_id = data.get('category_id')
    brand_id = data.get('brand_id')

    if not sku:
        category = Category.objects.filter(id=category_id).first() if category_id else None
        brand = Brand.objects.filter(id=brand_id).first() if brand_id else None
        sku = _generate_sku(category, brand)
        data['sku'] = sku

    if Product.objects.filter(sku=sku, is_deleted=False).exists():
        raise ValidationError("El SKU del producto ya existe.")
        
    product = Product.objects.create(**data)
    return product
def product_register(*, data: dict) -> Product:
    """Create a new product via API.
    Generates SKU if not provided, validates uniqueness, and returns the created Product.
    """
    # Reuse existing product_create logic which handles SKU generation and validation
    return product_create(data=data)


def product_soft_delete(*, product: Product):
    product.is_deleted = True
    product.save(update_fields=['is_deleted'])

def process_product_scan(*, barcode: str, channel_uuid: str):
    """
    Equivalente a App\\Events\\ProductScanned.
    Utiliza Django Channels para emitir al canal: scan_{channel_uuid}
    """
    product = Product.objects.filter(sku=barcode, is_deleted=False).first()
    
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
                "productData": product_data
            }
        )
    return product