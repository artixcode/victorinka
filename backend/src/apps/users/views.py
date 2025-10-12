from rest_framework import views, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, MeSerializer

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response({"detail": "Аккаунт создан"}, status=status.HTTP_201_CREATED)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

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

    def get(self, request):
        return Response(MeSerializer(request.user).data)

class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.data.get("refresh"):
            return Response({"detail": "Refresh токен обязателен"}, status=400)
        return Response({"detail": "Вы вышли из системы"})
