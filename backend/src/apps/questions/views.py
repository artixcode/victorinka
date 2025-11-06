from rest_framework import generics, permissions
from .models import Question, Quiz, Topic, Tag
from .serializers import (
    QuestionSerializer,
    QuizListSerializer,
    QuizDetailSerializer,
    QuizCreateSerializer,
    TopicSerializer,
    TagSerializer
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class IsAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id


class TopicListView(generics.ListAPIView):
    """Список всех тем"""
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [permissions.AllowAny]


class TagListView(generics.ListAPIView):
    """Список всех тегов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class MyQuestionsListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Question.objects.filter(author=self.request.user).order_by("-created_at")

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["text", "difficulty", "options"],
            properties={
                "text": openapi.Schema(type=openapi.TYPE_STRING, example="Столица Франции?"),
                "explanation": openapi.Schema(type=openapi.TYPE_STRING, example="Подсказка/пояснение (опционально)"),
                "difficulty": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["easy", "medium", "hard"],
                    example="easy",
                ),
                "points": openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                "options": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    minItems=4,
                    maxItems=4,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "text": openapi.Schema(type=openapi.TYPE_STRING),
                            "is_correct": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            "order": openapi.Schema(type=openapi.TYPE_INTEGER),
                        },
                        required=["text", "is_correct", "order"],
                    ),
                    example=[
                        {"text": "Париж", "is_correct": True, "order": 1},
                        {"text": "Берлин", "is_correct": False, "order": 2},
                        {"text": "Рим", "is_correct": False, "order": 3},
                        {"text": "Мадрид", "is_correct": False, "order": 4},
                    ],
                ),
            },
        )
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
                "difficulty": "medium",
                "points": 5,
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



class MyQuizzesListCreateView(generics.ListCreateAPIView):
    """Мои викторины (список и создание)"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return QuizCreateSerializer
        return QuizListSerializer

    def get_queryset(self):
        return Quiz.objects.filter(author=self.request.user).order_by("-created_at")

    @swagger_auto_schema(
        request_body=QuizCreateSerializer,
        responses={201: QuizListSerializer},
        examples={
            "application/json": {
                "title": "География Европы",
                "description": "Тест на знание столиц европейских стран",
                "status": "draft",
                "visibility": "public",
                "topic_ids": [1, 2],
                "tag_ids": [3, 4],
                "question_orders": [
                    {"question_id": 10, "order": 1},
                    {"question_id": 11, "order": 2},
                    {"question_id": 12, "order": 3}
                ]
            }
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MyQuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальный просмотр/редактирование/удаление моей викторины"""
    serializer_class = QuizDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthor]
    queryset = Quiz.objects.all()

    @swagger_auto_schema(request_body=QuizDetailSerializer)
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(request_body=QuizDetailSerializer)
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class PublicQuizzesListView(generics.ListAPIView):
    """Публичные опубликованные викторины (каталог)"""
    serializer_class = QuizListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Quiz.objects.filter(
            status=Quiz.Status.PUBLISHED,
            visibility=Quiz.Visibility.PUBLIC
        ).order_by("-created_at")

        # Фильтрация по темам
        topics = self.request.query_params.get("topics")
        if topics:
            topic_ids = [int(t) for t in topics.split(",") if t.isdigit()]
            queryset = queryset.filter(topics__id__in=topic_ids).distinct()

        # Фильтрация по тегам
        tags = self.request.query_params.get("tags")
        if tags:
            tag_ids = [int(t) for t in tags.split(",") if t.isdigit()]
            queryset = queryset.filter(tags__id__in=tag_ids).distinct()

        # Поиск по названию
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("topics", openapi.IN_QUERY, description="ID тем через запятую (например: 1,2,3)", type=openapi.TYPE_STRING),
            openapi.Parameter("tags", openapi.IN_QUERY, description="ID тегов через запятую (например: 1,2,3)", type=openapi.TYPE_STRING),
            openapi.Parameter("search", openapi.IN_QUERY, description="Поиск по названию", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicQuizDetailView(generics.RetrieveAPIView):
    """Детальный просмотр публичной викторины"""
    serializer_class = QuizDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Quiz.objects.filter(
            status=Quiz.Status.PUBLISHED,
            visibility=Quiz.Visibility.PUBLIC
        )
