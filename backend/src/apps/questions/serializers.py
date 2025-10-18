from django.db import transaction
from django.db.models import Count
from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator

from .models import Question, AnswerOption


class AnswerOptionInSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    text = serializers.CharField(max_length=300)
    is_correct = serializers.BooleanField()
    order = serializers.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)])


class QuestionSerializer(serializers.ModelSerializer):
    options = AnswerOptionInSerializer(many=True, write_only=True)
    options_readonly = serializers.SerializerMethodField(read_only=True)
    points = serializers.IntegerField(min_value=1, max_value=100, required=False)

    class Meta:
        model = Question
        fields = ["id", "text", "explanation", "difficulty", "points", "options", "options_readonly", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_options_readonly(self, obj):
        opts = obj.options.order_by("order", "id").values("id", "text", "is_correct", "order")
        return list(opts)

    def validate_options(self, value):
        if not value:
            raise serializers.ValidationError("Нужно добавить хотя бы один вариант.")
        if len(value) > 4:
            raise serializers.ValidationError("Максимум 4 варианта ответа.")
        orders = [item.get("order") for item in value]
        if any(o is None or o < 1 or o > 4 for o in orders):
            raise serializers.ValidationError("Поле 'order' у вариантов должно быть от 1 до 4.")
        if len(set(orders)) != len(orders):
            raise serializers.ValidationError("Порядок (order) вариантов не должен повторяться.")
        correct_count = sum(1 for item in value if item.get("is_correct") is True)
        if correct_count != 1:
            raise serializers.ValidationError("Должен быть ровно один правильный вариант.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        options = validated_data.pop("options")
        q = Question.objects.create(author=user, **validated_data)
        AnswerOption.objects.bulk_create([
            AnswerOption(question=q, **opt) for opt in options
        ])
        return q

    @transaction.atomic
    def update(self, instance, validated_data):
        options = validated_data.pop("options", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if options is not None:
            instance.options.all().delete()
            AnswerOption.objects.bulk_create([
                AnswerOption(question=instance, **opt) for opt in options
            ])
        return instance
