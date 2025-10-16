from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Question
from .serializers import QuestionSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class IsAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id


class MyQuestionsListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Question.objects.filter(author=self.request.user).order_by("-created_at")

    @swagger_auto_schema(
        request_body=QuestionSerializer,
        examples={
            "application/json": {
                "title": "Столица Франции?",
                "difficulty": 2,
                "options": [
                    {"text": "Париж", "is_correct": True, "order": 1},
                    {"text": "Берлин", "is_correct": False, "order": 2},
                    {"text": "Рим", "is_correct": False, "order": 3},
                    {"text": "Мадрид", "is_correct": False, "order": 4},
                ]
            }
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MyQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthor]
    queryset = Question.objects.all()

    @swagger_auto_schema(
        request_body=QuestionSerializer,
        examples={
            "application/json": {
                "title": "Столица Германии?",
                "difficulty": 3,
                "options": [
                    {"text": "Берлин", "is_correct": True,  "order": 1},
                    {"text": "Гамбург", "is_correct": False, "order": 2},
                ]
            }
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(request_body=QuestionSerializer)
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
