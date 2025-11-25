import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { quizzesAPI } from '../services/quizzesAPI';
import styles from '../styles/QuizView.module.css';

const QuizView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }

    if (id) {
      fetchQuiz();
    } else {
      setError('ID викторины не указан');
      setLoading(false);
    }
  }, [id]);

  const fetchQuiz = async () => {
    try {
      setLoading(true);

      let response;
      try {
        response = await quizzesAPI.getQuiz(id);
        setQuiz(response.data);
        return; // Если успешно, выходим
      } catch (publicError) {
        // Если 404, проверяем авторизацию и пробуем через эндпоинт автора
        if (publicError.response?.status === 404) {
          const userData = localStorage.getItem('user');
          if (!userData) {
            setError('Викторина не найдена или не опубликована');
            return;
          }

          // Пробуем получить через эндпоинт автора
          try {
            response = await quizzesAPI.getMyQuiz(id);
            setQuiz(response.data);
          } catch (myQuizError) {
            if (myQuizError.response?.status === 404 || myQuizError.response?.status === 403) {
              setError('Викторина не найдена или у вас нет доступа');
            } else {
              setError('Ошибка загрузки викторины');
            }
          }
        } else {
          setError('Ошибка загрузки викторины');
        }
      }
    } catch (err) {
      console.error('Error fetching quiz:', err);
      setError('Ошибка загрузки викторины');
    } finally {
      setLoading(false);
    }
  };

  const handleStartGame = () => {
    navigate('/create-room', { state: { quizId: id } });
  };

  if (loading) {
    return (
      <div className={styles.pageContainer}>
        <Header />
        <main className={styles.main}>
          <div className={styles.loading}>Загрузка викторины...</div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !quiz) {
    return (
      <div className={styles.pageContainer}>
        <Header />
        <main className={styles.main}>
          <div className={styles.error}>
            <h2>Ошибка загрузки</h2>
            <p>{error}</p>
            <div className={styles.errorActions}>
              <Link to="/quizzes" className={styles.backButton}>
                ← К каталогу викторин
              </Link>
              {user && (
                <Link to="/my-quizzes" className={styles.myQuizzesButton}>
                  📝 Мои викторины
                </Link>
              )}
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const isAuthor = user && quiz.author === user.id;
  const isPublished = quiz.status === 'published';

  return (
    <div className={styles.pageContainer}>
      <Header />
      <main className={styles.main}>
        <div className={styles.quizHeader}>
          <Link to="/quizzes" className={styles.backLink}>
            ← Назад к каталогу
          </Link>

          <div className={styles.quizTitleSection}>
            <h1 className={styles.title}>{quiz.title}</h1>
            <div className={styles.quizMeta}>
              <span className={`${styles.status} ${styles[quiz.status]}`}>
                {quiz.status === 'published' ? '📢 Опубликована' : '📝 Черновик'}
              </span>
              {!isPublished && isAuthor && (
                <span className={styles.authorNote}>
                  👋 Это ваша викторина в черновике
                </span>
              )}
              {!isPublished && !isAuthor && (
                <span className={styles.warning}>
                  ⚠️ Эта викторина не опубликована
                </span>
              )}
            </div>
          </div>

          <div className={styles.authorInfo}>
            <span className={styles.author}>
              Автор: {quiz.author_name || 'Аноним'}
            </span>
            {isAuthor && (
              <Link to="/my-quizzes" className={styles.manageLink}>
                Управление →
              </Link>
            )}
          </div>
        </div>

        <div className={styles.quizContent}>
          <div className={styles.infoCard}>
            <h3>Описание викторины</h3>
            <p className={styles.description}>
              {quiz.description || 'Описание отсутствует'}
            </p>
          </div>

          <div className={styles.statsGrid}>
            <div className={styles.statCard}>
              <div className={styles.statIcon}>❓</div>
              <div className={styles.statInfo}>
                <span className={styles.statNumber}>
                  {quiz.questions_list ? quiz.questions_list.length : quiz.question_count || 0}
                </span>
                <span className={styles.statLabel}>вопросов</span>
              </div>
            </div>

            <div className={styles.statCard}>
              <div className={styles.statIcon}>👁️</div>
              <div className={styles.statInfo}>
                <span className={styles.statNumber}>{quiz.views_count || 0}</span>
                <span className={styles.statLabel}>просмотров</span>
              </div>
            </div>

            <div className={styles.statCard}>
              <div className={styles.statIcon}>📅</div>
              <div className={styles.statInfo}>
                <span className={styles.statNumber}>
                  {new Date(quiz.created_at).toLocaleDateString('ru-RU')}
                </span>
                <span className={styles.statLabel}>создана</span>
              </div>
            </div>
          </div>

          {quiz.topics && quiz.topics.length > 0 && (
            <div className={styles.infoCard}>
              <h3>Темы</h3>
              <div className={styles.topics}>
                {quiz.topics.map(topic => (
                  <span key={topic.id} className={styles.topic}>
                    {topic.name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {quiz.tags && quiz.tags.length > 0 && (
            <div className={styles.infoCard}>
              <h3>Теги</h3>
              <div className={styles.tags}>
                {quiz.tags.map(tag => (
                  <span key={tag.id} className={styles.tag}>
                    #{tag.name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {quiz.questions_list && quiz.questions_list.length > 0 && (
            <div className={styles.infoCard}>
              <h3>Вопросы ({quiz.questions_list.length})</h3>
              <div className={styles.questionsList}>
                {quiz.questions_list.map((question, index) => (
                  <div key={question.id} className={styles.questionItem}>
                    <div className={styles.questionHeader}>
                      <span className={styles.questionNumber}>Вопрос {index + 1}</span>
                      <span className={`${styles.difficulty} ${styles[question.difficulty]}`}>
                        {question.difficulty === 'easy' ? '🟢 Легкий' :
                         question.difficulty === 'medium' ? '🟡 Средний' : '🔴 Сложный'}
                      </span>
                      <span className={styles.points}>🎯 {question.points} баллов</span>
                    </div>
                    <p className={styles.questionText}>{question.text}</p>
                    {question.explanation && (
                      <div className={styles.explanation}>
                        <strong>Объяснение:</strong> {question.explanation}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className={styles.actions}>
          {isPublished ? (
            <div className={styles.publishedActions}>
              <button onClick={handleStartGame} className={styles.startButton}>
                🎮 Создать комнату и начать игру
              </button>
              <p className={styles.helpText}>
                Создайте игровую комнату, чтобы начать викторину с друзьями
              </p>
            </div>
          ) : (
            <div className={styles.draftActions}>
              <div className={styles.draftMessage}>
                <h3>Викторина в черновике</h3>
                <p>
                  {isAuthor
                    ? 'Опубликуйте викторину в разделе "Мои викторины", чтобы другие пользователи могли в неё играть'
                    : 'Эта викторина находится в черновике и доступна только автору'
                  }
                </p>
              </div>
              {isAuthor && (
                <div className={styles.authorActions}>
                  <Link to="/my-quizzes" className={styles.manageButton}>
                    📝 Управление викторинами
                  </Link>
                  <button
                    onClick={() => navigate('/create-room', { state: { quizId: id } })}
                    className={styles.testButton}
                  >
                    🧪 Тестовый запуск
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default QuizView;