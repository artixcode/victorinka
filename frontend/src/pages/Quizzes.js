import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { Link } from 'react-router-dom';
import styles from '../styles/Quizzes.module.css';
import { quizzesAPI } from '../services/quizzesAPI';
import { cabinetAPI } from '../services/cabinetAPI';

const Quizzes = () => {
  const [user, setUser] = useState(null);
  const [quizzes, setQuizzes] = useState([]);
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const quizzesPerPage = 16;

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }

    fetchQuizzes();
    if (userData) {
      fetchBookmarks();
    }
  }, []);

  const fetchQuizzes = async () => {
    try {
      setLoading(true);
      const response = await quizzesAPI.getPublicQuizzes();
      const quizzesData = response.data.results || [];
      setQuizzes(quizzesData);
    } catch (err) {
      setError('Ошибка загрузки викторин');
      setQuizzes([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchBookmarks = async () => {
    try {
      const response = await cabinetAPI.getBookmarks();

      let bookmarksData = [];
      if (Array.isArray(response.data)) {
        bookmarksData = response.data;
      } else if (response.data && Array.isArray(response.data.results)) {
        bookmarksData = response.data.results;
      } else {
        bookmarksData = [];
      }

      setBookmarks(bookmarksData);
    } catch (err) {
      setBookmarks([]);
    }
  };

  const isQuizBookmarked = (quizId) => {
    if (!Array.isArray(bookmarks)) {
      return false;
    }
    return bookmarks.some(bookmark => {
      const bookmarkQuizId = bookmark.quiz || bookmark.quiz_id;
      return bookmarkQuizId === quizId;
    });
  };

  const getBookmarkId = (quizId) => {
    if (!Array.isArray(bookmarks)) return null;

    const bookmark = bookmarks.find(b => {
      const bookmarkQuizId = b.quiz || bookmark.quiz_id;
      return bookmarkQuizId === quizId;
    });
    return bookmark ? bookmark.id : null;
  };

  const handleBookmark = async (quizId) => {
    if (!user) {
      alert('Для добавления в закладки необходимо авторизоваться');
      return;
    }

    try {
      const isCurrentlyBookmarked = isQuizBookmarked(quizId);

      if (isCurrentlyBookmarked) {
        const bookmarkId = getBookmarkId(quizId);
        if (bookmarkId) {
          await cabinetAPI.deleteBookmark(bookmarkId);
          setBookmarks(bookmarks.filter(b => {
            const bookmarkQuizId = b.quiz || b.quiz_id;
            return bookmarkQuizId !== quizId;
          }));
        }
      } else {
        await cabinetAPI.addBookmark({ quiz: quizId });
        await fetchBookmarks();
      }

    } catch (err) {
      await fetchBookmarks();
      alert('Ошибка при обновлении закладки');
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
      <div>
        <Header />
        <main className={styles.main}>
          <div className={styles.loading}>Загрузка викторин...</div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Header />
        <main className={styles.main}>
          <div className={styles.error}>{error}</div>
          <button onClick={fetchQuizzes} className={styles.retryButton}>
            Попробовать снова
          </button>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div>
      <Header />
      <main className={styles.main}>
        <div className={styles.headerSection}>
          <h1 className={styles.title}>Каталог викторин</h1>
          <p className={styles.subtitle}>Выберите викторину по интересам и проверьте свои знания</p>

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

            {user && (
              <Link to="/create-quiz" className={styles.createButton}>
                + Создать викторину
              </Link>
            )}
          </div>
        </div>

        <div className={styles.quizzesGrid}>
          {currentQuizzes.map(quiz => {
            const isBookmarked = isQuizBookmarked(quiz.id);

            return (
              <div key={quiz.id} className={styles.quizCard}>
                <div className={styles.quizHeader}>
                  <button
                    onClick={() => handleBookmark(quiz.id)}
                    className={`${styles.bookmarkButton} ${isBookmarked ? styles.bookmarked : ''}`}
                    title={isBookmarked ? 'Удалить из закладок' : 'Добавить в закладки'}
                  >
                    {isBookmarked ? '★' : '☆'}
                  </button>

                  <div className={styles.quizMeta}>
                    <span className={styles.status}>
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
                      👁️ {quiz.views_count || 0}
                    </span>
                  </div>

                  <div className={styles.quizFooter}>
                    <span className={styles.author}>
                      Автор: {quiz.author_name || 'Аноним'}
                    </span>
                    <Link to={`/quiz/${quiz.id}`} className={styles.startButton}>
                      Начать
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {filteredQuizzes.length === 0 && !loading && (
          <div className={styles.emptyState}>
            <h3>Викторины не найдены</h3>
            <p>Попробуйте изменить поисковый запрос</p>
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

            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
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
      <Footer />
    </div>
  );
};

export default Quizzes;