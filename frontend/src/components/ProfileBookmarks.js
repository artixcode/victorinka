import React, { useState, useEffect } from 'react';
import { cabinetAPI } from '../services/cabinetAPI';
import styles from '../styles/ProfileBookmarks.module.css';

const ProfileBookmarks = () => {
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadBookmarks();
  }, []);

  const loadBookmarks = async () => {
    try {
      setLoading(true);
      const response = await cabinetAPI.getBookmarks();
      console.log('Bookmarks API response:', response); // Для отладки

      // Обрабатываем разные форматы ответа
      let bookmarksData = [];
      if (Array.isArray(response.data)) {
        bookmarksData = response.data;
      } else if (response.data && Array.isArray(response.data.results)) {
        bookmarksData = response.data.results;
      } else if (response.data && response.data.bookmarks) {
        bookmarksData = response.data.bookmarks;
      } else {
        // Если данные в другом формате, пробуем извлечь массив
        bookmarksData = Object.values(response.data).find(Array.isArray) || [];
      }

      setBookmarks(bookmarksData);
    } catch (error) {
      console.error('Ошибка загрузки закладок:', error);
      setError('Не удалось загрузить закладки');
      setBookmarks([]); // Устанавливаем пустой массив при ошибке
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBookmark = async (id) => {
    try {
      await cabinetAPI.deleteBookmark(id);
      setBookmarks(bookmarks.filter(bookmark => bookmark.id !== id));
    } catch (error) {
      console.error('Ошибка удаления закладки:', error);
      setError('Не удалось удалить закладку');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Дата не указана';
    try {
      return new Date(dateString).toLocaleDateString('ru-RU');
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return <div className={styles.loading}>Загрузка закладок...</div>;
  }

  return (
    <div className={styles.profileBookmarks}>
      <h1 className={styles.title}>Мои закладки</h1>

      {error && (
        <div className={styles.error}>
          {error}
        </div>
      )}

      {!Array.isArray(bookmarks) || bookmarks.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🔖</div>
          <h3>Закладок пока нет</h3>
          <p>Добавляйте понравившиеся викторины в закладки, чтобы легко найти их позже!</p>
        </div>
      ) : (
        <div className={styles.bookmarksList}>
          {bookmarks.map((bookmark) => (
            <div key={bookmark.id} className={styles.bookmarkItem}>
              <div className={styles.bookmarkContent}>
                <h3 className={styles.quizTitle}>
                  {bookmark.quiz_title || bookmark.title || 'Без названия'}
                </h3>

                <div className={styles.quizInfo}>
                  <span className={styles.infoItem}>
                    👤 Автор: {bookmark.quiz_author || bookmark.author || 'Неизвестен'}
                  </span>
                  <span className={styles.infoItem}>
                    ❓ Вопросов: {bookmark.quiz_questions_count || bookmark.questions_count || 0}
                  </span>
                  <span className={styles.infoItem}>
                    👁️ Просмотров: {bookmark.quiz_views || bookmark.views || 0}
                  </span>
                </div>

                {bookmark.notes && (
                  <div className={styles.notes}>
                    <strong>Заметки:</strong> {bookmark.notes}
                  </div>
                )}

                <div className={styles.bookmarkFooter}>
                  <span className={styles.addedDate}>
                    Добавлено: {formatDate(bookmark.added_at || bookmark.created_at)}
                  </span>
                </div>
              </div>

              <div className={styles.bookmarkActions}>
                <button
                  className={styles.playButton}
                  onClick={() => {/* Навигация к викторине */}}
                >
                  Играть
                </button>
                <button
                  className={styles.deleteButton}
                  onClick={() => handleDeleteBookmark(bookmark.id)}
                >
                  Удалить
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProfileBookmarks;