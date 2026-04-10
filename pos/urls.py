from django.urls import path
from pos.api import LoginApi, RoleApi, PermissionApi, UserApi # type: ignore

urlpatterns = [
    path('auth/login', LoginApi.as_view(), name='auth-login'),
    path('roles', RoleApi.as_view(), name='roles'),
    path('roles/<int:pk>', RoleApi.as_view(), name='roles-detail'),
    path('permissions', PermissionApi.as_view(), name='permissions-list'),
    path('users', UserApi.as_view(), name='users'),
    path('users/<int:pk>', UserApi.as_view(), name='users-detail'),
]
