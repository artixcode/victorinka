from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Question
from .serializers import QuestionSerializer


class IsAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id


class MyQuestionsListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Question.objects.filter(author=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save()


class MyQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthor]
    queryset = Question.objects.all()
