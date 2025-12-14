from typing import Optional, List
from django.db.models import QuerySet

from apps.questions.domain.repositories import QuizRepository, QuestionRepository
from apps.questions.models import Quiz, Question, AnswerOption


class ORMQuizRepository(QuizRepository):
    def get_by_id(self, quiz_id: int) -> Optional[Quiz]:
        """Получить викторину по ID."""
        try:
            return Quiz.objects.prefetch_related(
                'questions',
                'topics',
                'tags'
            ).get(id=quiz_id)
        except Quiz.DoesNotExist:
            return None

    def create(self, author_id: int, title: str, **extra_fields) -> Quiz:
        """Создать новую викторину."""
        quiz = Quiz.objects.create(
            author_id=author_id,
            title=title,
            **extra_fields
        )
        return quiz

    def update(self, quiz: Quiz, **fields) -> Quiz:
        """Обновить викторину."""
        for field, value in fields.items():
            if field not in ['topics', 'tags']:
                setattr(quiz, field, value)

        # M2M поля
        if 'topics' in fields:
            quiz.topics.set(fields['topics'])
        if 'tags' in fields:
            quiz.tags.set(fields['tags'])

        quiz.save(update_fields=[f for f in fields.keys() if f not in ['topics', 'tags']])
        return quiz

    def delete(self, quiz: Quiz) -> None:
        """Удалить викторину."""
        quiz.delete()

    def get_user_quizzes(self, user_id: int) -> List[Quiz]:
        """Получить все викторины пользователя."""
        return list(
            Quiz.objects
            .filter(author_id=user_id)
            .prefetch_related('questions', 'topics', 'tags')
            .order_by('-created_at')
        )

    def get_published_quizzes(self, limit: int = 20) -> List[Quiz]:
        """Получить опубликованные викторины."""
        return list(
            Quiz.objects
            .filter(status=Quiz.Status.PUBLISHED)
            .select_related('author')
            .prefetch_related('topics', 'tags')
            .order_by('-created_at')[:limit]
        )


class ORMQuestionRepository(QuestionRepository):

    def get_by_id(self, question_id: int) -> Optional[Question]:
        """Получить вопрос по ID."""
        try:
            return Question.objects.prefetch_related('options').get(id=question_id)
        except Question.DoesNotExist:
            return None

    def create(
        self,
        author_id: int,
        text: str,
        difficulty: str,
        points: int,
        **extra_fields
    ) -> Question:
        """Создать новый вопрос."""
        question = Question.objects.create(
            author_id=author_id,
            text=text,
            difficulty=difficulty,
            points=points,
            **extra_fields
        )
        return question

    def update(self, question: Question, **fields) -> Question:
        """Обновить вопрос."""
        for field, value in fields.items():
            setattr(question, field, value)
        question.save(update_fields=list(fields.keys()))
        return question

    def delete(self, question: Question) -> None:
        """Удалить вопрос."""
        question.delete()

    def get_user_questions(self, user_id: int) -> List[Question]:
        """Получить все вопросы пользователя."""
        return list(
            Question.objects
            .filter(author_id=user_id)
            .prefetch_related('options')
            .order_by('-created_at')
        )

    def add_option(self, question: Question, text: str, is_correct: bool, order: int) -> AnswerOption:
        """Добавить вариант ответа к вопросу."""
        option = AnswerOption.objects.create(
            question=question,
            text=text,
            is_correct=is_correct,
            order=order
        )
        return option

quiz_repository = ORMQuizRepository()
question_repository = ORMQuestionRepository()

