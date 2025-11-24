import pytest
from model_bakery import baker
from apps.questions.models import Question, AnswerOption

@pytest.mark.django_db
def test_create_question_with_options(auth_client):
    payload = {
        "text": "2+2?",
        "points": 10,
        "options": [
            {"text": "3", "is_correct": False, "order": 1},
            {"text": "4", "is_correct": True,  "order": 2},
            {"text": "5", "is_correct": False, "order": 3},
            {"text": "22","is_correct": False, "order": 4},
        ],
    }
    res = auth_client.post("/api/questions/", payload, format="json")
    assert res.status_code == 201, res.data
    q = Question.objects.get(id=res.data["id"])
    assert q.points == 10
    assert AnswerOption.objects.filter(question=q, is_correct=True).count() == 1

@pytest.mark.django_db
def test_list_my_questions(auth_client):
    res = auth_client.get("/api/questions/")
    assert res.status_code == 200
