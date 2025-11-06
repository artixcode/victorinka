from django.db import transaction
from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator

from .models import Question, AnswerOption, Quiz, Topic, Tag, QuizQuestion


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name", "slug"]
        read_only_fields = ["id", "slug"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]
        read_only_fields = ["id", "slug"]


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


class QuizQuestionSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    order = serializers.IntegerField(min_value=0)


class QuizListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.nickname", read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id", "title", "description", "author", "author_name",
            "status", "visibility", "topics", "tags",
            "question_count", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_question_count(self, obj):
        return obj.questions.count()


class QuizDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.nickname", read_only=True)
    topics = TopicSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    questions_list = serializers.SerializerMethodField()

    topic_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    question_orders = QuizQuestionSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Quiz
        fields = [
            "id", "title", "description", "author", "author_name",
            "status", "visibility",
            "topics", "tags", "topic_ids", "tag_ids",
            "questions_list", "question_orders",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_questions_list(self, obj):
        quiz_questions = QuizQuestion.objects.filter(quiz=obj).select_related("question").order_by("order")
        return [
            {
                "id": qq.question.id,
                "text": qq.question.text,
                "difficulty": qq.question.difficulty,
                "points": qq.question.points,
                "order": qq.order
            }
            for qq in quiz_questions
        ]

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        topic_ids = validated_data.pop("topic_ids", [])
        tag_ids = validated_data.pop("tag_ids", [])
        question_orders = validated_data.pop("question_orders", [])

        quiz = Quiz.objects.create(author=user, **validated_data)

        if topic_ids:
            quiz.topics.set(Topic.objects.filter(id__in=topic_ids))
        if tag_ids:
            quiz.tags.set(Tag.objects.filter(id__in=tag_ids))

        if question_orders:
            self._update_quiz_questions(quiz, question_orders, user)

        return quiz

    @transaction.atomic
    def update(self, instance, validated_data):
        topic_ids = validated_data.pop("topic_ids", None)
        tag_ids = validated_data.pop("tag_ids", None)
        question_orders = validated_data.pop("question_orders", None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if topic_ids is not None:
            instance.topics.set(Topic.objects.filter(id__in=topic_ids))
        if tag_ids is not None:
            instance.tags.set(Tag.objects.filter(id__in=tag_ids))

        if question_orders is not None:
            self._update_quiz_questions(instance, question_orders, self.context["request"].user)

        return instance

    def _update_quiz_questions(self, quiz, question_orders, user):
        QuizQuestion.objects.filter(quiz=quiz).delete()

        question_ids = [qo["question_id"] for qo in question_orders]
        valid_questions = Question.objects.filter(id__in=question_ids, author=user)
        valid_ids = set(valid_questions.values_list("id", flat=True))

        quiz_questions = []
        for qo in question_orders:
            if qo["question_id"] in valid_ids:
                quiz_questions.append(
                    QuizQuestion(
                        quiz=quiz,
                        question_id=qo["question_id"],
                        order=qo["order"]
                    )
                )

        if quiz_questions:
            QuizQuestion.objects.bulk_create(quiz_questions)


class QuizCreateSerializer(serializers.ModelSerializer):
    topic_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    question_orders = QuizQuestionSerializer(many=True, required=False, allow_empty=True)

    class Meta:
        model = Quiz
        fields = ["title", "description", "status", "visibility", "topic_ids", "tag_ids", "question_orders"]

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        topic_ids = validated_data.pop("topic_ids", [])
        tag_ids = validated_data.pop("tag_ids", [])
        question_orders = validated_data.pop("question_orders", [])

        quiz = Quiz.objects.create(author=user, **validated_data)

        if topic_ids:
            quiz.topics.set(Topic.objects.filter(id__in=topic_ids))
        if tag_ids:
            quiz.tags.set(Tag.objects.filter(id__in=tag_ids))

        if question_orders:
            self._add_questions(quiz, question_orders, user)

        return quiz

    def _add_questions(self, quiz, question_orders, user):

        question_ids = [qo["question_id"] for qo in question_orders]
        valid_questions = Question.objects.filter(id__in=question_ids, author=user)
        valid_ids = set(valid_questions.values_list("id", flat=True))

        quiz_questions = []
        for qo in question_orders:
            if qo["question_id"] in valid_ids:
                quiz_questions.append(
                    QuizQuestion(
                        quiz=quiz,
                        question_id=qo["question_id"],
                        order=qo["order"]
                    )
                )

        if quiz_questions:
            QuizQuestion.objects.bulk_create(quiz_questions)

