from rest_framework import views, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, MeSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={201: openapi.Response("Аккаунт создан", RegisterSerializer)}
    )
    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(RegisterSerializer(user).data, status=status.HTTP_201_CREATED)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: openapi.Response("OK", LoginSerializer)}
    )
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })

class MeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={200: MeSerializer})
    def get(self, request):
        return Response(MeSerializer(request.user).data)

class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.data.get("refresh"):
            return Response({"detail": "Refresh токен обязателен"}, status=400)
        return Response({"detail": "Вы вышли из системы"})
