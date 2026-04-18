from django.urls import path, re_path
from pos.api import LoginApi, RoleApi, PermissionApi, UserApi, BrandApi, CategoryApi
from pos.api.products import ProductApi, ProductDetailApi, ProductConfigApi, ProductScanApi
from .import consumers

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────
    path('auth/login', LoginApi.as_view(), name='auth-login'),

    # ── Access ────────────────────────────────────────────
    path('roles', RoleApi.as_view(), name='roles'),
    path('roles/<int:pk>', RoleApi.as_view(), name='roles-detail'),
    path('permissions', PermissionApi.as_view(), name='permissions-list'),
    path('users', UserApi.as_view(), name='users'),
    path('users/<int:pk>', UserApi.as_view(), name='users-detail'),

    # ── Catalog: Brands ──────────────────────────────────
    path('catalog/brands', BrandApi.as_view(), name='brand-list'),
    path('catalog/brands/<int:pk>', BrandApi.as_view(), name='brand-detail'),

    # ── Catalog: Categories ──────────────────────────────
    path('catalog/categories', CategoryApi.as_view(), name='category-list'),
    path('catalog/categories/<int:pk>', CategoryApi.as_view(), name='category-detail'),
    
    # --- Products ---
    path('products/config', ProductConfigApi.as_view(), name='product-config'),
    path('products/scan', ProductScanApi.as_view(), name='product-scan'),
    path('products', ProductApi.as_view(), name='product-list'),
    path('products/<int:pk>', ProductDetailApi.as_view(), name='product-detail'),
]

# WebSocket URL 
websocket_urlpatterns = [
    re_path(r'ws/scan/(?P<channel_uuid>[0-9a-f-]+)/$', consumers.ScanConsumer.as_asgi()),
]