import pytest
from model_bakery import baker
from apps.questions.models import Topic, Tag, Quiz, Question


@pytest.mark.django_db
def test_topics_list(api):
    Topic.objects.all().delete()  # сброс

    baker.make(Topic, _quantity=3)

    res = api.get("/api/topics/")

    assert res.status_code == 200
    assert res.data["count"] == 3
    assert len(res.data["results"]) == 3



@pytest.mark.django_db
def test_tags_list(api):
    Tag.objects.all().delete()
    baker.make(Tag, _quantity=4)

    res = api.get("/api/tags/")

    assert res.status_code == 200
    assert len(res.data) == 4


@pytest.mark.django_db
def test_public_quizzes_list(api, user):

    # создаём квизы с author=user
    baker.make(
        Quiz,
        author=user,
        status="published",
        visibility="public",
        _quantity=2
    )

    baker.make(Quiz, author=user, status="draft", visibility="public")
    baker.make(Quiz, author=user, status="published", visibility="private")

    res = api.get("/api/quizzes/")

    assert res.status_code == 200
    assert res.data["count"] == 2


@pytest.mark.django_db
def test_public_quiz_detail(api, user):
    quiz = baker.make(
        Quiz,
        author=user,
        status="published",
        visibility="public",
    )

    q1 = baker.make(Question)
    q1.in_quizzes.add(quiz)

    res = api.get(f"/api/quizzes/{quiz.id}/")

    assert res.status_code == 200
    assert res.data["id"] == quiz.id
    assert "title" in res.data
    assert "questions_list" in res.data


@pytest.mark.django_db
def test_home_page_top10(api, user):
    Quiz.objects.all().delete()

    for i in range(12):
        baker.make(
            Quiz,
            author=user,
            status="published",
            visibility="public",
            views_count=i,
        )

    res = api.get("/api/home/")

    assert res.status_code == 200
    assert len(res.data) == 10

    views = [item["views_count"] for item in res.data]
    assert views == sorted(views, reverse=True)
