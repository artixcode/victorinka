from abc import ABC, abstractmethod
from typing import Optional, List


class QuizRepository(ABC):
    @abstractmethod
    def get_by_id(self, quiz_id: int):
        """Получить викторину по ID."""
        pass

    @abstractmethod
    def create(self, author_id: int, title: str, **extra_fields):
        """Создать новую викторину."""
        pass

    @abstractmethod
    def update(self, quiz, **fields):
        """Обновить викторину."""
        pass

    @abstractmethod
    def delete(self, quiz) -> None:
        """Удалить викторину."""
        pass

    @abstractmethod
    def get_user_quizzes(self, user_id: int) -> List:
        """Получить все викторины пользователя."""
        pass

    @abstractmethod
    def get_published_quizzes(self, limit: int = 20) -> List:
        """Получить опубликованные викторины."""
        pass


class QuestionRepository(ABC):
    """
    Абстрактный репозиторий для работы с вопросами.
    """

    @abstractmethod
    def get_by_id(self, question_id: int):
        """Получить вопрос по ID."""
        pass

    @abstractmethod
    def create(
        self,
        author_id: int,
        text: str,
        difficulty: str,
        points: int,
        **extra_fields
    ):
        """Создать новый вопрос."""
        pass

    @abstractmethod
    def update(self, question, **fields):
        """Обновить вопрос."""
        pass

    @abstractmethod
    def delete(self, question) -> None:
        """Удалить вопрос."""
        pass

    @abstractmethod
    def get_user_questions(self, user_id: int) -> List:
        """Получить все вопросы пользователя."""
        pass

