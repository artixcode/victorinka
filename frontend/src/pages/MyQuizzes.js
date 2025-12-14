import React, {useState, useEffect} from 'react';
import {useNavigate, Link} from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import {quizzesAPI} from '../services/quizzesAPI';
import styles from '../styles/Quizzes.module.css';

const MyQuizzes = () => {
    const navigate = useNavigate();
    const [quizzes, setQuizzes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [searchQuery, setSearchQuery] = useState('');
    const quizzesPerPage = 16;

    useEffect(() => {
        const userData = localStorage.getItem('user');
        if (userData) {
            fetchMyQuizzes();
        } else {
            navigate('/login');
        }
    }, [navigate]);

    const fetchMyQuizzes = async () => {
        try {
            setLoading(true);
            const response = await quizzesAPI.getMyQuizzes();
            const quizzesData = response.data.results || response.data || [];
            setQuizzes(quizzesData);
        } catch (err) {
            setError('Ошибка загрузки ваших викторин');
            setQuizzes([]);
        } finally {
            setLoading(false);
        }
    };

    const handleStatusChange = async (quizId, newStatus) => {
        try {
            await quizzesAPI.patchMyQuiz(quizId, {status: newStatus});
            setQuizzes(quizzes.map(quiz =>
                quiz.id === quizId ? {...quiz, status: newStatus} : quiz
            ));
        } catch (err) {
            alert('Ошибка при изменении статуса');
        }
    };

    const handleDeleteQuiz = async (quizId) => {
        if (!window.confirm('Вы уверены, что хотите удалить эту викторину?')) {
            return;
        }

        try {
            await quizzesAPI.deleteMyQuiz(quizId);
            setQuizzes(quizzes.filter(quiz => quiz.id !== quizId));
        } catch (err) {
            alert('Ошибка при удалении викторины');
        }
    };

    const filteredQuizzes = quizzes.filter(quiz =>
        quiz.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        quiz.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (quiz.topics && quiz.topics.some(topic =>
            topic.name?.toLowerCase().includes(searchQuery.toLowerCase())
        ))
    );

    const indexOfLastQuiz = currentPage * quizzesPerPage;
    const indexOfFirstQuiz = indexOfLastQuiz - quizzesPerPage;
    const currentQuizzes = filteredQuizzes.slice(indexOfFirstQuiz, indexOfLastQuiz);
    const totalPages = Math.ceil(filteredQuizzes.length / quizzesPerPage);
    const paginate = (pageNumber) => setCurrentPage(pageNumber);

    if (loading) {
        return (
            <div className={styles.pageContainer}>
                <Header/>
                <main className={styles.main}>
                    <div className={styles.loading}>Загрузка ваших викторин...</div>
                </main>
                <Footer/>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.pageContainer}>
                <Header/>
                <main className={styles.main}>
                    <div className={styles.error}>{error}</div>
                    <button onClick={fetchMyQuizzes} className={styles.retryButton}>
                        Попробовать снова
                    </button>
                </main>
                <Footer/>
            </div>
        );
    }

    return (
        <div className={styles.pageContainer}>
            <Header/>
            <main className={styles.main}>
                <div className={styles.headerSection}>
                    <h1 className={styles.title}>Мои викторины</h1>
                    <p className={styles.subtitle}>Управляйте созданными викторинами и их статусами</p>

                    <div className={styles.controls}>
                        <div className={styles.searchContainer}>
                            <input
                                type="text"
                                placeholder="Поиск по названию, описанию или темам..."
                                value={searchQuery}
                                onChange={(e) => {
                                    setSearchQuery(e.target.value);
                                    setCurrentPage(1);
                                }}
                                className={styles.searchInput}
                            />
                            <span className={styles.searchIcon}>🔍</span>
                        </div>

                        <div className={styles.userControls}>
                            <Link to="/quizzes" className={styles.backButton}>
                                ← К викторинам
                            </Link>
                            <button
                                onClick={() => navigate('/create-quiz')}
                                className={styles.createButton}
                            >
                                + Создать викторину
                            </button>
                        </div>
                    </div>
                </div>

                <div className={styles.quizzesGrid}>
                    {currentQuizzes.map(quiz => (
                        <div key={quiz.id} className={styles.quizCard}>
                            <div className={styles.quizHeader}>
                                <div className={styles.quizActions}>
                                    <button
                                        onClick={() => handleDeleteQuiz(quiz.id)}
                                        className={styles.deleteButton}
                                        title="Удалить"
                                    >
                                        🗑️
                                    </button>
                                </div>

                                <div className={styles.quizMeta}>
                  <span className={`${styles.status} ${styles[quiz.status]}`}>
                    {quiz.status === 'published' ? 'Опубликована' : 'Черновик'}
                  </span>
                                </div>
                            </div>

                            <div className={styles.quizContent}>
                                <h3 className={styles.quizTitle}>{quiz.title}</h3>
                                <p className={styles.quizDescription}>
                                    {quiz.description || 'Описание отсутствует'}
                                </p>

                                {quiz.topics && quiz.topics.length > 0 && (
                                    <div className={styles.topics}>
                                        {quiz.topics.slice(0, 3).map(topic => (
                                            <span key={topic.id} className={styles.topic}>
                        {topic.name}
                      </span>
                                        ))}
                                        {quiz.topics.length > 3 && (
                                            <span className={styles.topic}>+{quiz.topics.length - 3}</span>
                                        )}
                                    </div>
                                )}

                                <div className={styles.quizStats}>
                  <span className={styles.stat}>
                    ❓ {quiz.question_count || 0} вопросов
                  </span>
                                    <span className={styles.stat}>
                    👁️ {quiz.views_count || 0} просмотров
                  </span>
                                </div>
                            </div>

                            <div className={styles.quizFooter}>
                <span className={styles.author}>
                  Автор: {quiz.author_name || 'Вы'}
                </span>
                                <div className={styles.quizControls}>
                                    {quiz.status === 'draft' && (
                                        <button
                                            onClick={() => handleStatusChange(quiz.id, 'published')}
                                            className={styles.publishButton}
                                        >
                                            Опубликовать
                                        </button>
                                    )}
                                    {quiz.status === 'published' && (
                                        <button
                                            onClick={() => handleStatusChange(quiz.id, 'draft')}
                                            className={styles.unpublishButton}
                                        >
                                            В черновик
                                        </button>
                                    )}
                                    <Link to={`/quiz/${quiz.id}`} className={styles.startButton}>
                                        Продолжить
                                    </Link>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {filteredQuizzes.length === 0 && !loading && (
                    <div className={styles.emptyState}>
                        <h3>Викторины не найдены</h3>
                        <p>Попробуйте изменить поисковый запрос или создайте первую викторину</p>
                        <button
                            onClick={() => navigate('/create-quiz')}
                            className={styles.retryButton}
                        >
                            Создать первую викторину
                        </button>
                    </div>
                )}

                {totalPages > 1 && (
                    <div className={styles.pagination}>
                        <button
                            onClick={() => paginate(currentPage - 1)}
                            disabled={currentPage === 1}
                            className={styles.paginationButton}
                        >
                            ← Назад
                        </button>

                        {Array.from({length: totalPages}, (_, i) => i + 1).map(page => (
                            <button
                                key={page}
                                onClick={() => paginate(page)}
                                className={`${styles.paginationButton} ${currentPage === page ? styles.active : ''}`}
                            >
                                {page}
                            </button>
                        ))}

                        <button
                            onClick={() => paginate(currentPage + 1)}
                            disabled={currentPage === totalPages}
                            className={styles.paginationButton}
                        >
                            Вперед →
                        </button>
                    </div>
                )}
            </main>
            <Footer/>
        </div>
    );
};

export default MyQuizzes;