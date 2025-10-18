from django import forms
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.contrib import admin
from .models import Topic, Tag, Quiz, Question, AnswerOption, QuizQuestion


class AnswerOptionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        forms_valid = [f for f in self.forms if not f.cleaned_data.get("DELETE", False) and not f.errors]

        if len(forms_valid) == 0:
            raise ValidationError("Добавьте хотя бы один вариант ответа.")
        if len(forms_valid) > 4:
            raise ValidationError("Максимум 4 варианта ответа на вопрос.")

        correct_count = sum(1 for f in forms_valid if f.cleaned_data.get("is_correct") is True)
        if correct_count != 1:
            raise ValidationError("Должен быть ровно 1 правильный вариант ответа.")

        orders = [f.cleaned_data.get("order") for f in forms_valid if f.cleaned_data.get("order") is not None]
        if any(o < 1 or o > 4 for o in orders):
            raise ValidationError("Поле 'order' должно быть от 1 до 4.")
        if len(orders) != len(set(orders)):
            raise ValidationError("Порядок (order) вариантов внутри вопроса не должен повторяться.")


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    formset = AnswerOptionInlineFormSet
    extra = 2
    max_num = 4
    min_num = 1
    can_delete = True
    fields = ("text", "is_correct", "order")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "short_text", "author", "difficulty", "points", "created_at")
    list_filter = ("difficulty", "points")
    search_fields = ("text",)
    raw_id_fields = ("author",)
    inlines = [AnswerOptionInline]

    def short_text(self, obj):
        return (obj.text[:80] + "…") if len(obj.text) > 80 else obj.text
