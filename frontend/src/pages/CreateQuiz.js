import React, {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import QuestionForm from '../components/QuestionForm';
import {quizzesAPI} from '../services/quizzesAPI';
import {questionsAPI} from '../services/questionsAPI';
import styles from '../styles/CreateQuiz.module.css';

const CreateQuiz = () => {
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
    const [loading, setLoading] = useState(false);

    const handleQuizChange = (field, value) => {
        setQuiz({...quiz, [field]: value});
    };

    const handleAddQuestion = (questionData) => {
        if (editingQuestion !== null) {
            // Редактирование существующего вопроса
            const newQuestions = [...questions];
            newQuestions[editingQuestion] = questionData;
            setQuestions(newQuestions);
            setEditingQuestion(null);
        } else {
            // Добавление нового вопроса
            setQuestions([...questions, {...questionData, id: Date.now()}]);
        }
        setShowQuestionForm(false);
    };

    const handleEditQuestion = (index) => {
        setEditingQuestion(index);
        setShowQuestionForm(true);
    };

    const handleDeleteQuestion = (index) => {
        const newQuestions = questions.filter((_, i) => i !== index);
        setQuestions(newQuestions);
    };

    const handleSaveQuiz = async () => {
        if (!quiz.title.trim()) {
            alert('Введите название викторины');
            return;
        }

        if (questions.length === 0) {
            alert('Добавьте хотя бы один вопрос');
            return;
        }

        setLoading(true);

        try {
            const createdQuestions = [];
            for (const question of questions) {
                const response = await questionsAPI.createQuestion({
                    text: question.text,
                    explanation: question.explanation,
                    difficulty: question.difficulty,
                    points: question.points,
                    options: question.options
                });
                createdQuestions.push(response.data);
            }

            const questionOrders = createdQuestions.map((question, index) => ({
                question_id: question.id,
                order: index
            }));

            const quizResponse = await quizzesAPI.createQuiz({
                title: quiz.title,
                description: quiz.description,
                status: quiz.status,
                visibility: quiz.visibility,
                question_orders: questionOrders
            });

            alert('Викторина успешно создана!');
            navigate('/quizzes');

        } catch (error) {
            alert('Ошибка при создании викторины');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const moveQuestion = (fromIndex, toIndex) => {
        const newQuestions = [...questions];
        const [movedQuestion] = newQuestions.splice(fromIndex, 1);
        newQuestions.splice(toIndex, 0, movedQuestion);
        setQuestions(newQuestions);
    };

    return (
        <div>
            <Header/>
            <main className={styles.main}>
                <div className={styles.container}>
                    <h1 className={styles.title}>Создание викторины</h1>

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
                                            <h4>{question.text}</h4>
                                            <div className={styles.questionMeta}>
                        <span className={styles.difficulty}>
                          {question.difficulty === 'easy' ? '🟢 Лёгкий' :
                              question.difficulty === 'medium' ? '🟡 Средний' : '🔴 Сложный'}
                        </span>
                                                <span className={styles.points}>🎯 {question.points} баллов</span>
                                            </div>
                                            <div className={styles.optionsPreview}>
                                                {question.options.map((option, optIndex) => (
                                                    <span
                                                        key={optIndex}
                                                        className={`${styles.optionPreview} ${option.is_correct ? styles.correct : ''}`}
                                                    >
                            {option.is_correct ? '✓ ' : ''}{option.text}
                          </span>
                                                ))}
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
                            onClick={() => navigate('/quizzes')}
                            className={styles.cancelButton}
                        >
                            Отмена
                        </button>
                        <button
                            onClick={handleSaveQuiz}
                            disabled={loading || questions.length === 0 || !quiz.title.trim()}
                            className={styles.saveButton}
                        >
                            {loading ? 'Создание...' : 'Создать викторину'}
                        </button>
                    </div>
                </div>
            </main>
            <Footer/>
        </div>
    );
};

export default CreateQuiz;