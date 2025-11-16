from rest_framework import serializers
from .models import GameSession, GameRound, PlayerAnswer, PlayerGameStats
from apps.users.serializers import MeSerializer as UserSerializer
from apps.questions.serializers import QuestionSerializer


class GameSessionSerializer(serializers.ModelSerializer):
    """Сериализатор для игровой сессии"""

    room_name = serializers.CharField(source='room.name', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    total_questions = serializers.SerializerMethodField()
    current_round = serializers.SerializerMethodField()
    players_count = serializers.SerializerMethodField()

    class Meta:
        model = GameSession
        fields = [
            'id',
            'room',
            'room_name',
            'quiz',
            'quiz_title',
            'status',
            'current_question_index',
            'total_questions',
            'current_round',
            'players_count',
            'started_at',
            'finished_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'started_at', 'finished_at']

    def get_total_questions(self, obj):
        return obj.quiz.questions.count()

    def get_current_round(self, obj):
        if obj.status in [GameSession.Status.PLAYING, GameSession.Status.PAUSED]:
            try:
                current_round = obj.rounds.get(round_number=obj.current_question_index + 1)
                return GameRoundSerializer(current_round).data
            except GameRound.DoesNotExist:
                return None
        return None

    def get_players_count(self, obj):
        return obj.player_stats.count()


class GameRoundSerializer(serializers.ModelSerializer):

    question_data = QuestionSerializer(source='question', read_only=True)
    answers_count = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()

    class Meta:
        model = GameRound
        fields = [
            'id',
            'session',
            'question',
            'question_data',
            'round_number',
            'time_limit',
            'status',
            'first_answer_user',
            'answers_count',
            'time_remaining',
            'started_at',
            'completed_at',
        ]
        read_only_fields = ['id', 'started_at', 'completed_at']

    def get_answers_count(self, obj):
        return obj.answers.count()

    def get_time_remaining(self, obj):
        if obj.status == GameRound.Status.ACTIVE and obj.started_at:
            from django.utils import timezone
            elapsed = (timezone.now() - obj.started_at).total_seconds()
            remaining = max(0, obj.time_limit - elapsed)
            return round(remaining, 1)
        return None


class PlayerAnswerSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа игрока"""

    user_data = UserSerializer(source='user', read_only=True)
    selected_option_text = serializers.CharField(source='selected_option.text', read_only=True)

    class Meta:
        model = PlayerAnswer
        fields = [
            'id',
            'round',
            'user',
            'user_data',
            'selected_option',
            'selected_option_text',
            'is_correct',
            'points_earned',
            'time_taken',
            'answered_at',
        ]
        read_only_fields = ['id', 'is_correct', 'points_earned', 'answered_at']


class PlayerAnswerCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ответа игрока"""

    class Meta:
        model = PlayerAnswer
        fields = ['selected_option']

    def validate_selected_option(self, value):
        round_id = self.context.get('round_id')
        if not round_id:
            raise serializers.ValidationError("Round ID not provided in context")

        try:
            game_round = GameRound.objects.get(id=round_id)
        except GameRound.DoesNotExist:
            raise serializers.ValidationError("Round not found")

        if value.question_id != game_round.question_id:
            raise serializers.ValidationError(
                "Selected option does not belong to the current question"
            )

        return value

    def create(self, validated_data):
        """Создаем ответ с автоматическим расчетом очков"""
        from django.utils import timezone

        round_obj = self.context['round']
        user = self.context['user']
        selected_option = validated_data['selected_option']

        if round_obj.started_at:
            time_taken = (timezone.now() - round_obj.started_at).total_seconds()
        else:
            time_taken = 0

        answer = PlayerAnswer.objects.create(
            round=round_obj,
            user=user,
            selected_option=selected_option,
            is_correct=selected_option.is_correct,
            time_taken=time_taken
        )

        answer.calculate_points()
        answer.save()

        if answer.is_correct and not round_obj.first_answer_user:
            round_obj.first_answer_user = user
            round_obj.save(update_fields=['first_answer_user'])

        stats, _ = PlayerGameStats.objects.get_or_create(
            session=round_obj.session,
            user=user
        )
        stats.update_from_answer(answer)

        return answer


class PlayerGameStatsSerializer(serializers.ModelSerializer):
    """Сериализатор для статистики игрока"""

    user_data = UserSerializer(source='user', read_only=True)
    accuracy = serializers.SerializerMethodField()
    total_answers = serializers.SerializerMethodField()

    class Meta:
        model = PlayerGameStats
        fields = [
            'id',
            'session',
            'user',
            'user_data',
            'total_points',
            'correct_answers',
            'wrong_answers',
            'total_answers',
            'accuracy',
            'rank',
            'completed_at',
        ]
        read_only_fields = ['id', 'completed_at']

    def get_accuracy(self, obj):
        """Процент правильных ответов"""
        total = obj.correct_answers + obj.wrong_answers
        if total == 0:
            return 0
        return round((obj.correct_answers / total) * 100, 1)

    def get_total_answers(self, obj):
        return obj.correct_answers + obj.wrong_answers


class GameStartSerializer(serializers.Serializer):
    """Сериализатор для запуска игры"""

    quiz_id = serializers.IntegerField(required=True)

    def validate_quiz_id(self, value):
        from apps.questions.models import Quiz

        try:
            quiz = Quiz.objects.get(id=value)
        except Quiz.DoesNotExist:
            raise serializers.ValidationError("Quiz not found")

        if quiz.status != Quiz.Status.PUBLISHED:
            raise serializers.ValidationError("Quiz is not published")

        if quiz.questions.count() == 0:
            raise serializers.ValidationError("Quiz has no questions")

        return value


class GameResultsSerializer(serializers.Serializer):
    """Сериализатор для результатов игры"""

    session = GameSessionSerializer()
    leaderboard = PlayerGameStatsSerializer(many=True)
    total_rounds = serializers.IntegerField()
    completed_rounds = serializers.IntegerField()

    class Meta:
        fields = ['session', 'leaderboard', 'total_rounds', 'completed_rounds']

