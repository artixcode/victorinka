from typing import List, Dict
from django.db import transaction

from apps.questions.domain.value_objects.question_text import QuestionText
from apps.questions.domain.value_objects.difficulty import Difficulty


class CreateQuestionService:
    """
    Application Service для создания вопроса.
    """

    @transaction.atomic
    def execute(
        self,
        author_id: int,
        text: str,
        difficulty: str,
        options: List[Dict[str, any]],
        explanation: str = "",
        points: int = None
    ):
        """
        Создать новый вопрос.
        """
        from apps.questions.models import Question, AnswerOption

        # 1. Валидация текста через Value Object
        question_text_vo = QuestionText(text)

        # 2. Валидация сложности через Value Object
        difficulty_vo = Difficulty.from_string(difficulty)

        # 3. Определение очков
        if points is None:
            points = difficulty_vo.recommended_points()

        if points <= 0:
            raise ValueError("Очки должны быть больше 0")

        # 4. Валидация вариантов ответа
        self._validate_options(options)

        # 5. Создание вопроса
        question = Question.objects.create(
            author_id=author_id,
            text=question_text_vo.value,
            difficulty=difficulty_vo.level.value,
            points=points,
            explanation=explanation
        )

        # 6. Создание вариантов ответа
        for idx, option_data in enumerate(options, start=1):
            AnswerOption.objects.create(
                question=question,
                text=option_data['text'],
                is_correct=option_data.get('is_correct', False),
                order=option_data.get('order', idx)
            )

        return question

    def _validate_options(self, options: List[Dict]) -> None:
        """
        Валидация вариантов ответа.
        """
        if not options:
            raise ValueError("Необходимо указать варианты ответа")

        if len(options) < 2:
            raise ValueError("Минимум 2 варианта ответа")

        if len(options) > 6:
            raise ValueError("Максимум 6 вариантов ответа")

        # Проверка правильных ответов
        correct_count = sum(1 for opt in options if opt.get('is_correct', False))

        if correct_count == 0:
            raise ValueError("Необходимо указать правильный ответ")

        if correct_count > 1:
            raise ValueError(
                f"Должен быть только 1 правильный ответ, указано {correct_count}"
            )

        # Проверка текста вариантов
        for idx, option in enumerate(options, start=1):
            text = option.get('text', '').strip()
            if not text:
                raise ValueError(f"Вариант №{idx}: текст не может быть пустым")

            if len(text) > 300:
                raise ValueError(
                    f"Вариант №{idx}: текст слишком длинный "
                    f"(максимум 300 символов, сейчас {len(text)})"
                )

