from django.db import transaction

from apps.questions.domain.services.quiz_validation_service import (
    QuizValidationService,
    QuizValidationException
)


class PublishQuizService:
    """
    Application Service для публикации викторины.
    """

    def __init__(self, validation_service: QuizValidationService = None):
        """
        Инициализация сервиса.
        """
        self.validation_service = validation_service or QuizValidationService()

    @transaction.atomic
    def execute(self, quiz_id: int, user_id: int) -> dict:
        """
        Опубликовать викторину.
        """
        from apps.questions.models import Quiz

        # 1. Получение викторины
        try:
            quiz = Quiz.objects.prefetch_related(
                'questions__options',
                'quizquestion_set__question__options'
            ).get(id=quiz_id)
        except Quiz.DoesNotExist:
            raise ValueError(f"Викторина с ID {quiz_id} не найдена")

        # 2. Проверка прав
        if quiz.author_id != user_id:
            raise PermissionError("Только автор может опубликовать викторину")

        # 3. Проверка текущего статуса
        if quiz.status == Quiz.Status.PUBLISHED:
            return {
                "success": True,
                "quiz_id": quiz.id,
                "message": "Викторина уже опубликована"
            }

        # 4. Валидация через Domain Service
        self.validation_service.validate_or_raise(quiz)

        # 5. Публикация
        quiz.publish()

        return {
            "success": True,
            "quiz_id": quiz.id,
            "message": "Викторина успешно опубликована",
            "questions_count": quiz.questions.count()
        }

    def validate(self, quiz_id: int) -> dict:
        """
        Проверить готовность викторины к публикации без изменения статуса.
        """
        from apps.questions.models import Quiz

        try:
            quiz = Quiz.objects.prefetch_related(
                'questions__options',
                'quizquestion_set__question__options'
            ).get(id=quiz_id)
        except Quiz.DoesNotExist:
            return {
                "is_valid": False,
                "errors": [f"Викторина с ID {quiz_id} не найдена"]
            }

        is_valid, errors = self.validation_service.validate_for_publication(quiz)

        return {
            "is_valid": is_valid,
            "errors": errors,
            "quiz_id": quiz.id,
            "title": quiz.title,
            "questions_count": quiz.questions.count()
        }

