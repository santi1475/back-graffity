from django.urls import path
from pos.api import LoginApi, RoleApi, PermissionApi, UserApi, BrandApi, CategoryApi

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
]