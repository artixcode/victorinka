from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import ActiveSession, QuizBookmark, GameHistory, PasswordResetToken

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(validators=[UniqueValidator(queryset=User.objects.all())])
    nickname = serializers.CharField(max_length = 40,
    validators = [UniqueValidator(queryset=User.objects.all(), lookup="iexact")],
    )
    class Meta:
        model = User
        fields = ("id", "email", "password", "nickname")
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Неверный email или пароль")
        if not user.is_active:
            raise serializers.ValidationError("Пользователь деактивирован")
        attrs["user"] = user
        return attrs

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "nickname", "is_email_verified", "total_wins", "total_points")
        read_only_fields = fields

class ActiveSessionOutSerializer(serializers.ModelSerializer):
    device = serializers.SerializerMethodField()

    class Meta:
        model = ActiveSession
        fields = ("id", "refresh_jti", "ip", "user_agent", "device", "created_at", "last_seen_at")
        read_only_fields = fields

    def get_device(self, obj):
        ua = (obj.user_agent or "").lower()
        if "iphone" in ua or "ios" in ua: return "iOS"
        if "android" in ua: return "Android"
        if "mac os" in ua or "macintosh" in ua: return "macOS"
        if "windows" in ua: return "Windows"
        if "linux" in ua: return "Linux"
        return "Unknown"

class ProfileUpdateSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(max_length = 40,
    validators=[UniqueValidator(queryset=User.objects.all(), lookup="iexact")],
    )

    class Meta:
        model = User
        fields = ("nickname",)


class QuizBookmarkSerializer(serializers.ModelSerializer):
    """Сериализатор для закладок викторин"""

    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    quiz_author = serializers.CharField(source='quiz.author.nickname', read_only=True)
    quiz_questions_count = serializers.SerializerMethodField()
    quiz_views = serializers.IntegerField(source='quiz.views_count', read_only=True)

    class Meta:
        model = QuizBookmark
        fields = [
            'id',
            'quiz',
            'quiz_title',
            'quiz_author',
            'quiz_questions_count',
            'quiz_views',
            'added_at',
            'notes',
        ]
        read_only_fields = ['id', 'added_at']

    def get_quiz_questions_count(self, obj):
        return obj.quiz.questions.count()


class QuizBookmarkCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания закладки"""

    class Meta:
        model = QuizBookmark
        fields = ['quiz', 'notes']

    def validate_quiz(self, value):
        if value.status != 'published':
            raise serializers.ValidationError("Можно добавлять в закладки только опубликованные викторины")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class GameHistorySerializer(serializers.ModelSerializer):
    """Сериализатор для истории игр"""

    quiz_title = serializers.CharField(source='quiz.title', read_only=True, default="Викторина удалена")
    room_name = serializers.CharField(source='room.name', read_only=True)
    accuracy = serializers.ReadOnlyField()

    class Meta:
        model = GameHistory
        fields = [
            'id',
            'session',
            'room_name',
            'quiz',
            'quiz_title',
            'final_points',
            'correct_answers',
            'total_questions',
            'accuracy',
            'final_rank',
            'played_at',
        ]
        read_only_fields = fields


class UserStatsSerializer(serializers.ModelSerializer):
    """Сериализатор для статистики пользователя"""

    total_games = serializers.SerializerMethodField()
    bookmarks_count = serializers.SerializerMethodField()
    active_rooms_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'nickname',
            'total_wins',
            'total_points',
            'total_games',
            'bookmarks_count',
            'active_rooms_count',
        ]
        read_only_fields = fields

    def get_total_games(self, obj):
        return obj.game_history.count()

    def get_bookmarks_count(self, obj):
        return obj.quiz_bookmarks.count()

    def get_active_rooms_count(self, obj):
        from apps.rooms.models import Room
        return Room.objects.filter(
            participants__user=obj,
            status__in=[Room.Status.OPEN, Room.Status.IN_PROGRESS]
        ).count()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса восстановления пароля"""
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким email не найден")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Сериализатор для подтверждения восстановления пароля с токеном"""
    token = serializers.CharField(max_length=64)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_token(self, value):
        try:
            reset_token = PasswordResetToken.objects.get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Токен не найден")

        if not reset_token.is_valid():
            if reset_token.is_used:
                raise serializers.ValidationError("Токен уже использован")
            if reset_token.is_expired():
                raise serializers.ValidationError("Токен истек. Запросите новый токен восстановления")

        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен содержать минимум 8 символов")
        return value


class PasswordResetTokenSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения токена восстановления (для админов)"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_valid_token = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()

    class Meta:
        model = PasswordResetToken
        fields = [
            'id',
            'user',
            'user_email',
            'token',
            'created_at',
            'expires_at',
            'is_used',
            'used_at',
            'is_valid_token',
            'time_left',
        ]
        read_only_fields = fields

    def get_is_valid_token(self, obj):
        return obj.is_valid()

    def get_time_left(self, obj):
        """Возвращает оставшееся время в часах"""
        if obj.is_used or obj.is_expired():
            return 0
        from django.utils import timezone
        delta = obj.expires_at - timezone.now()
        hours = delta.total_seconds() / 3600
        return round(hours, 1)

