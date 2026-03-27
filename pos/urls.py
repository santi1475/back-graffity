from django.urls import path

from pos.apis import LoginApi

urlpatterns = [
    path('auth/login', LoginApi.as_view(), name='auth-login'),
]
