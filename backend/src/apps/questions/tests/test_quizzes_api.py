import pytest
from model_bakery import baker
from apps.questions.models import Quiz, Question, Topic, Tag, QuizQuestion

@pytest.mark.django_db
def test_my_quizzes_list(auth_client, user):

    my_quiz1 = baker.make("questions.Quiz", author=user)
    my_quiz2 = baker.make("questions.Quiz", author=user)

    other_user = baker.make("users.User")
    baker.make("questions.Quiz", author=other_user)

    res = auth_client.get("/api/quizzes/mine/")

    assert res.status_code == 200
    assert res.data["count"] == 2

    returned_ids = {q["id"] for q in res.data["results"]}
    assert returned_ids == {my_quiz1.id, my_quiz2.id}

@pytest.mark.django_db
def test_create_quiz_with_topics_tags_questions(auth_client, user):

    topic1 = baker.make(Topic)
    topic2 = baker.make(Topic)
    tag1 = baker.make(Tag)
    tag2 = baker.make(Tag)

    q1 = baker.make(Question, author=user)
    q2 = baker.make(Question, author=user)

    payload = {
        "title": "География Европы",
        "description": "Тест по географии",
        "status": "draft",
        "visibility": "public",
        "topic_ids": [topic1.id, topic2.id],
        "tag_ids": [tag1.id, tag2.id],
        "question_orders": [
            {"question_id": q1.id, "order": 1},
            {"question_id": q2.id, "order": 2},
        ],
    }

    res = auth_client.post("/api/quizzes/mine/", payload, format="json")

    assert res.status_code == 201

    assert res.data["title"] == "География Европы"
    assert res.data["description"] == "Тест по географии"
    assert res.data["status"] == "draft"
    assert res.data["visibility"] == "public"

    # Ищем созданную викторину
    quiz = Quiz.objects.get(title="География Европы", author=user)

    assert quiz.topics.count() == 2
    assert quiz.tags.count() == 2
    assert quiz.questions.count() == 2


@pytest.mark.django_db
def test_my_quiz_detail_questions_list(auth_client, user):

    quiz = baker.make(Quiz, author=user)

    q1 = baker.make(Question, author=user)
    q2 = baker.make(Question, author=user)

    QuizQuestion.objects.create(quiz=quiz, question=q1, order=2)
    QuizQuestion.objects.create(quiz=quiz, question=q2, order=1)

    res = auth_client.get(f"/api/quizzes/mine/{quiz.id}/")

    assert res.status_code == 200
    assert res.data["id"] == quiz.id
    assert res.data["title"] == quiz.title

    questions_list = res.data["questions_list"]
    assert len(questions_list) == 2

    # Должны быть отсортированы по order
    orders = [item["order"] for item in questions_list]
    assert orders == sorted(orders)


@pytest.mark.django_db
def test_update_quiz_title_and_questions(auth_client, user):

    quiz = baker.make(Quiz, author=user, title="Old title")

    q1 = baker.make(Question, author=user)
    q2 = baker.make(Question, author=user)

    QuizQuestion.objects.create(quiz=quiz, question=q1, order=1)
    QuizQuestion.objects.create(quiz=quiz, question=q2, order=2)

    payload = {
        "title": "New title",
        "question_orders": [
            {"question_id": q1.id, "order": 2},
            {"question_id": q2.id, "order": 1},
        ],
    }

    res = auth_client.patch(f"/api/quizzes/mine/{quiz.id}/", payload, format="json")

    assert res.status_code == 200
    quiz.refresh_from_db()
    assert quiz.title == "New title"

    quiz_questions = QuizQuestion.objects.filter(quiz=quiz).order_by("order")
    orders = [qq.order for qq in quiz_questions]
    question_ids = [qq.question_id for qq in quiz_questions]

    assert orders == [1, 2]
    assert set(question_ids) == {q1.id, q2.id}


@pytest.mark.django_db
def test_delete_my_quiz(auth_client, user):

    quiz = baker.make(Quiz, author=user)

    res = auth_client.delete(f"/api/quizzes/mine/{quiz.id}/")

    assert res.status_code == 204
    assert not Quiz.objects.filter(id=quiz.id).exists()


@pytest.mark.django_db
def test_public_quizzes_list_only_published_public(api):

    author = baker.make("users.User")

    q1 = baker.make(
        Quiz,
        author=author,
        status=Quiz.Status.PUBLISHED,
        visibility=Quiz.Visibility.PUBLIC,
    )
    q2 = baker.make(
        Quiz,
        author=author,
        status=Quiz.Status.PUBLISHED,
        visibility=Quiz.Visibility.PUBLIC,
    )

    baker.make(
        Quiz,
        author=author,
        status=Quiz.Status.DRAFT,
        visibility=Quiz.Visibility.PUBLIC,
    )
    baker.make(
        Quiz,
        author=author,
        status=Quiz.Status.PUBLISHED,
        visibility=Quiz.Visibility.PRIVATE,
    )

    res = api.get("/api/quizzes/")

    assert res.status_code == 200
    ids = {item["id"] for item in res.data["results"]}
    assert ids == {q1.id, q2.id}
    for item in res.data["results"]:
        assert item["status"] == Quiz.Status.PUBLISHED
        assert item["visibility"] == Quiz.Visibility.PUBLIC


@pytest.mark.django_db
def test_public_quiz_detail_increments_views(api):

    author = baker.make("users.User")
    quiz = baker.make(
        Quiz,
        author=author,
        status=Quiz.Status.PUBLISHED,
        visibility=Quiz.Visibility.PUBLIC,
        views_count=0,
    )

    res = api.get(f"/api/quizzes/{quiz.id}/")

    assert res.status_code == 200
    quiz.refresh_from_db()
    assert quiz.views_count == 1
    assert res.data["views_count"] == 1
