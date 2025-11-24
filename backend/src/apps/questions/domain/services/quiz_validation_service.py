from typing import List, Tuple


class QuizValidationException(Exception):
    """Исключение при валидации викторины"""
    pass


class QuizValidationService:
    """
    Domain Service для валидации викторины перед публикацией.
    """

    MIN_QUESTIONS = 5
    MIN_OPTIONS_PER_QUESTION = 2
    MAX_OPTIONS_PER_QUESTION = 6

    def validate_for_publication(self, quiz) -> Tuple[bool, List[str]]:
        """
        Валидация викторины перед публикацией.
        """
        errors = []

        # 1. Проверка названия
        if not quiz.title or not quiz.title.strip():
            errors.append("Название викторины обязательно")

        # 2. Проверка количества вопросов
        questions_count = quiz.questions.count()
        if questions_count < self.MIN_QUESTIONS:
            errors.append(
                f"Недостаточно вопросов: {questions_count} "
                f"(минимум {self.MIN_QUESTIONS})"
            )

        # 3. Проверка каждого вопроса
        for idx, quiz_question in enumerate(quiz.quizquestion_set.select_related('question').all(), 1):
            question = quiz_question.question
            question_errors = self._validate_question(question, idx)
            errors.extend(question_errors)

        return (len(errors) == 0, errors)

    def _validate_question(self, question, question_num: int) -> List[str]:
        """
        Валидация отдельного вопроса.
        """
        errors = []
        prefix = f"Вопрос №{question_num}"

        # Проверка текста вопроса
        if not question.text or not question.text.strip():
            errors.append(f"{prefix}: текст вопроса обязателен")

        # Получаем варианты ответов
        options = list(question.options.all())
        options_count = len(options)

        # Проверка количества вариантов
        if options_count < self.MIN_OPTIONS_PER_QUESTION:
            errors.append(
                f"{prefix}: недостаточно вариантов ответа ({options_count}, "
                f"минимум {self.MIN_OPTIONS_PER_QUESTION})"
            )

        if options_count > self.MAX_OPTIONS_PER_QUESTION:
            errors.append(
                f"{prefix}: слишком много вариантов ответа ({options_count}, "
                f"максимум {self.MAX_OPTIONS_PER_QUESTION})"
            )

        # Проверка наличия правильного ответа
        correct_options = [opt for opt in options if opt.is_correct]

        if len(correct_options) == 0:
            errors.append(f"{prefix}: нет правильного ответа")
        elif len(correct_options) > 1:
            errors.append(
                f"{prefix}: несколько правильных ответов "
                f"({len(correct_options)}, должен быть только 1)"
            )

        # Проверка очков
        if question.points <= 0:
            errors.append(f"{prefix}: очки должны быть больше 0")

        return errors

    def can_publish(self, quiz) -> bool:
        """
        Быстрая проверка: можно ли опубликовать викторину.
        """
        is_valid, _ = self.validate_for_publication(quiz)
        return is_valid

    def validate_or_raise(self, quiz) -> None:
        """
        Валидация с выбросом исключения при ошибке.
        """
        is_valid, errors = self.validate_for_publication(quiz)

        if not is_valid:
            error_message = "Викторина не готова к публикации:\n" + "\n".join(
                f"- {error}" for error in errors
            )
            raise QuizValidationException(error_message)

