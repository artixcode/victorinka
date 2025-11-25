import pytest
from model_bakery import baker
from apps.questions.models import Question, AnswerOption

@pytest.mark.django_db
def test_my_questions_list(auth_client, user):
    q1 = baker.make("questions.Question", author=user)
    q2 = baker.make("questions.Question", author=user)

    res = auth_client.get("/api/questions/")

    assert res.status_code == 200
    assert res.data["count"] == 2
    assert len(res.data["results"]) == 2

@pytest.mark.django_db
def test_create_question(auth_client, user):
    payload = {
        "text": "Столица Франции?",
        "difficulty": "easy",
        "points": 5,
        "options": [
            {"text": "Париж", "is_correct": True, "order": 1},
            {"text": "Берлин", "is_correct": False, "order": 2},
            {"text": "Рим", "is_correct": False, "order": 3},
            {"text": "Мадрид", "is_correct": False, "order": 4},
        ],
    }

    res = auth_client.post("/api/questions/", payload, format="json")

    assert res.status_code == 201
    assert res.data["text"] == "Столица Франции?"
    assert res.data["difficulty"] == "easy"
    assert Question.objects.count() == 1
    assert AnswerOption.objects.count() == 4

@pytest.mark.django_db
def test_get_question_detail(auth_client, user):
    q = baker.make("questions.Question", author=user)
    baker.make("questions.AnswerOption", question=q)

    res = auth_client.get(f"/api/questions/{q.id}/")

    assert res.status_code == 200
    assert res.data["id"] == q.id
    assert res.data["text"] == q.text
@pytest.mark.django_db
def test_update_question(auth_client, user):
    q = baker.make("questions.Question", author=user)

    baker.make("questions.AnswerOption", question=q, order=1)
    baker.make("questions.AnswerOption", question=q, order=2)

    payload = {
        "text": "Новый текст вопроса",
        "difficulty": "hard",
        "points": 10,
        "options": [
            {"text": "A", "is_correct": True, "order": 1},
            {"text": "B", "is_correct": False, "order": 2},
            {"text": "C", "is_correct": False, "order": 3},
            {"text": "D", "is_correct": False, "order": 4},
        ],
    }

    res = auth_client.put(f"/api/questions/{q.id}/", payload, format="json")

    assert res.status_code == 200
    assert res.data["text"] == "Новый текст вопроса"
    assert AnswerOption.objects.filter(question=q).count() == 4


@pytest.mark.django_db
def test_delete_question(auth_client, user):
    q = baker.make("questions.Question", author=user)

    baker.make("questions.AnswerOption", question=q, order=1)
    baker.make("questions.AnswerOption", question=q, order=2)

    res = auth_client.delete(f"/api/questions/{q.id}/")

    assert res.status_code == 204
    assert not Question.objects.filter(id=q.id).exists()
