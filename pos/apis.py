from django.core.exceptions import ValidationError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from pos.services import auth_login


class LoginApi(APIView):
    """Endpoint público de autenticación por email y password."""

    authentication_classes = []
    permission_classes = []

    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        password = serializers.CharField()

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = auth_login(**serializer.validated_data)
        except ValidationError:
            return Response(
                {"message": "Credenciales inválidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(result, status=status.HTTP_200_OK)
