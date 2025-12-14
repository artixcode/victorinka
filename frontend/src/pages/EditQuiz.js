import React, {useState, useEffect} from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import QuestionForm from '../components/QuestionForm';
import {quizzesAPI} from '../services/quizzesAPI';
import {questionsAPI} from '../services/questionsAPI';
import styles from '../styles/CreateQuiz.module.css';

const EditQuiz = () => {
    const {id} = useParams();
    const navigate = useNavigate();
    const [quiz, setQuiz] = useState({
        title: '',
        description: '',
        status: 'draft',
        visibility: 'public'
    });
    const [questions, setQuestions] = useState([]);
    const [showQuestionForm, setShowQuestionForm] = useState(false);
    const [editingQuestion, setEditingQuestion] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetchQuizData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [id]);

    const fetchQuizData = async () => {
        try {
            setLoading(true);
            const quizResponse = await quizzesAPI.getMyQuiz(id);
            const quizData = quizResponse.data;

            setQuiz({
                title: quizData.title,
                description: quizData.description,
                status: quizData.status,
                visibility: quizData.visibility
            });

            if (quizData.questions_list && Array.isArray(quizData.questions_list)) {
                const questionsWithDetails = await Promise.all(
                    quizData.questions_list.map(async (q) => {
                        try {
                            const questionResponse = await questionsAPI.getQuestion(q.id);
                            return {
                                ...questionResponse.data,
                                options: Array.isArray(questionResponse.data.options_readonly)
                                    ? questionResponse.data.options_readonly
                                    : []
                            };
                        } catch (error) {
                            console.error(`Ошибка загрузки вопроса ${q.id}:`, error);
                            return {
                                ...q,
                                options: []
                            };
                        }
                    })
                );
                setQuestions(questionsWithDetails);
            } else {
                setQuestions([]);
            }
        } catch (err) {
            console.error('Ошибка загрузки викторины:', err);
            alert('Ошибка загрузки викторины');
            navigate('/my-quizzes');
        } finally {
            setLoading(false);
        }
    };

    const handleQuizChange = (field, value) => {
        setQuiz({...quiz, [field]: value});
    };

    const handleAddQuestion = (questionData) => {
        const questionWithDefaults = {
            ...questionData,
            options: Array.isArray(questionData.options) ? questionData.options : [],
            points: questionData.points || 1,
            difficulty: questionData.difficulty || 'medium'
        };

        if (editingQuestion !== null) {
            const newQuestions = [...questions];
            newQuestions[editingQuestion] = questionWithDefaults;
            setQuestions(newQuestions);
            setEditingQuestion(null);
        } else {
            setQuestions([...questions, {
                ...questionWithDefaults,
                id: `new-${Date.now()}`
            }]);
        }
        setShowQuestionForm(false);
    };

    const handleEditQuestion = (index) => {
        setEditingQuestion(index);
        setShowQuestionForm(true);
    };

    const handleDeleteQuestion = (index) => {
        const questionToDelete = questions[index];

        if (questionToDelete.id && !questionToDelete.id.toString().startsWith('new-')) {
            if (!window.confirm('Вы уверены, что хотите удалить этот вопрос?')) {
                return;
            }
        }

        const newQuestions = questions.filter((_, i) => i !== index);
        setQuestions(newQuestions);
    };

    const handleUpdateQuiz = async () => {
        if (!quiz.title.trim()) {
            alert('Введите название викторины');
            return;
        }

        if (questions.length === 0) {
            alert('Добавьте хотя бы один вопрос');
            return;
        }

        setSaving(true);

        try {
            await quizzesAPI.patchMyQuiz(id, {
                title: quiz.title,
                description: quiz.description,
                status: quiz.status,
                visibility: quiz.visibility
            });

            const questionOrders = [];

            for (let i = 0; i < questions.length; i++) {
                const question = questions[i];

                const questionData = {
                    text: question.text || '',
                    explanation: question.explanation || '',
                    difficulty: question.difficulty || 'medium',
                    points: parseInt(question.points) || 1,
                    options: Array.isArray(question.options) ? question.options.map((opt, index) => ({
                        text: opt.text || '',
                        is_correct: Boolean(opt.is_correct),
                        order: index + 1
                    })) : []
                };

                let questionId;

                if (question.id && question.id.toString().startsWith('new-')) {
                    try {
                        const response = await questionsAPI.createQuestion(questionData);
                        questionId = response.data.id;
                    } catch (error) {
                        console.error('Ошибка создания вопроса:', error);
                        continue;
                    }
                } else if (question.id) {
                    questionId = question.id;
                    try {
                        await questionsAPI.updateQuestion(question.id, questionData);
                    } catch (error) {
                        console.error('Ошибка обновления вопроса:', error);
                        try {
                            await questionsAPI.patchQuestion(question.id, questionData);
                        } catch (patchError) {
                            console.error('Ошибка частичного обновления вопроса:', patchError);
                        }
                    }
                }

                if (questionId) {
                    questionOrders.push({
                        question_id: questionId,
                        order: i
                    });
                }
            }

            if (questionOrders.length > 0) {
                await quizzesAPI.patchMyQuiz(id, {
                    question_orders: questionOrders
                });
            }

            alert('Викторина успешно обновлена!');
            navigate(`/quiz/${id}`);

        } catch (error) {
            console.error('Общая ошибка при обновлении викторины:', error);
            alert('Ошибка при обновлении викторины. Проверьте консоль для деталей.');
        } finally {
            setSaving(false);
        }
    };

    const moveQuestion = (fromIndex, toIndex) => {
        const newQuestions = [...questions];
        const [movedQuestion] = newQuestions.splice(fromIndex, 1);
        newQuestions.splice(toIndex, 0, movedQuestion);
        setQuestions(newQuestions);
    };

    const renderOptionsPreview = (question) => {
        const options = Array.isArray(question.options) ? question.options : [];

        if (options.length === 0) {
            return <span className={styles.optionPreview}>Нет вариантов ответа</span>;
        }

        return options.map((option, optIndex) => (
            <span
                key={optIndex}
                className={`${styles.optionPreview} ${option.is_correct ? styles.correct : ''}`}
            >
        {option.is_correct ? '✓ ' : ''}{option.text || 'Пустой вариант'}
      </span>
        ));
    };

    if (loading) {
        return (
            <div>
                <Header/>
                <main className={styles.main}>
                    <div style={{textAlign: 'center', padding: '4rem', color: 'white'}}>
                        Загрузка викторины...
                    </div>
                </main>
                <Footer/>
            </div>
        );
    }

    return (
        <div>
            <Header/>
            <main className={styles.main}>
                <div className={styles.container}>
                    <h1 className={styles.title}>Редактирование викторины</h1>

                    <div className={styles.quizInfo}>
                        <div className={styles.formGroup}>
                            <label>Название викторины *</label>
                            <input
                                type="text"
                                value={quiz.title}
                                onChange={(e) => handleQuizChange('title', e.target.value)}
                                placeholder="Введите название викторины..."
                                maxLength="140"
                            />
                        </div>

                        <div className={styles.formGroup}>
                            <label>Описание</label>
                            <textarea
                                value={quiz.description}
                                onChange={(e) => handleQuizChange('description', e.target.value)}
                                placeholder="Описание викторины..."
                                rows="3"
                            />
                        </div>

                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label>Статус</label>
                                <select
                                    value={quiz.status}
                                    onChange={(e) => handleQuizChange('status', e.target.value)}
                                >
                                    <option value="draft">Черновик</option>
                                    <option value="published">Опубликована</option>
                                </select>
                            </div>

                            <div className={styles.formGroup}>
                                <label>Видимость</label>
                                <select
                                    value={quiz.visibility}
                                    onChange={(e) => handleQuizChange('visibility', e.target.value)}
                                >
                                    <option value="public">Публичная</option>
                                    <option value="private">Приватная</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className={styles.questionsSection}>
                        <div className={styles.questionsHeader}>
                            <h2>Вопросы ({questions.length})</h2>
                            <button
                                onClick={() => setShowQuestionForm(true)}
                                className={styles.addQuestionButton}
                                disabled={showQuestionForm}
                            >
                                + Добавить вопрос
                            </button>
                        </div>

                        {showQuestionForm && (
                            <QuestionForm
                                onSave={handleAddQuestion}
                                onCancel={() => {
                                    setShowQuestionForm(false);
                                    setEditingQuestion(null);
                                }}
                                initialData={editingQuestion !== null ? questions[editingQuestion] : null}
                            />
                        )}

                        {questions.length === 0 ? (
                            <div className={styles.emptyQuestions}>
                                <p>Пока нет вопросов. Добавьте первый вопрос!</p>
                            </div>
                        ) : (
                            <div className={styles.questionsList}>
                                {questions.map((question, index) => (
                                    <div key={question.id || index} className={styles.questionItem}>
                                        <div className={styles.questionContent}>
                                            <h4>{question.text || 'Без текста'}</h4>
                                            <div className={styles.questionMeta}>
                        <span className={styles.difficulty}>
                          {question.difficulty === 'easy' ? '🟢 Лёгкий' :
                              question.difficulty === 'medium' ? '🟡 Средний' :
                                  question.difficulty === 'hard' ? '🔴 Сложный' : '⚪ Не указана'}
                        </span>
                                                <span className={styles.points}>🎯 {question.points || 0} баллов</span>
                                            </div>
                                            <div className={styles.optionsPreview}>
                                                {renderOptionsPreview(question)}
                                            </div>
                                        </div>
                                        <div className={styles.questionActions}>
                                            <button
                                                onClick={() => handleEditQuestion(index)}
                                                className={styles.editButton}
                                            >
                                                ✏️
                                            </button>
                                            <button
                                                onClick={() => handleDeleteQuestion(index)}
                                                className={styles.deleteButton}
                                            >
                                                🗑️
                                            </button>
                                            {index > 0 && (
                                                <button
                                                    onClick={() => moveQuestion(index, index - 1)}
                                                    className={styles.moveButton}
                                                >
                                                    ↑
                                                </button>
                                            )}
                                            {index < questions.length - 1 && (
                                                <button
                                                    onClick={() => moveQuestion(index, index + 1)}
                                                    className={styles.moveButton}
                                                >
                                                    ↓
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className={styles.actions}>
                        <button
                            onClick={() => navigate(`/quiz/${id}`)}
                            className={styles.cancelButton}
                        >
                            Отмена
                        </button>
                        <button
                            onClick={handleUpdateQuiz}
                            disabled={saving || questions.length === 0 || !quiz.title.trim()}
                            className={styles.saveButton}
                        >
                            {saving ? 'Сохранение...' : 'Сохранить изменения'}
                        </button>
                    </div>
                </div>
            </main>
            <Footer/>
        </div>
    );
};

export default EditQuiz;