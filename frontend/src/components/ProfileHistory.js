import React, { useState, useEffect } from 'react';
import { cabinetAPI } from '../services/cabinetAPI';
import styles from '../styles/ProfileHistory.module.css';

const ProfileHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await cabinetAPI.getHistory();
      console.log('History API response:', response); // Для отладки
      
      // Обрабатываем разные форматы ответа
      let historyData = [];
      if (Array.isArray(response.data)) {
        historyData = response.data;
      } else if (response.data && Array.isArray(response.data.results)) {
        historyData = response.data.results;
      } else if (response.data && response.data.history) {
        historyData = response.data.history;
      } else if (response.data && response.data.games) {
        historyData = response.data.games;
      } else {
        // Если данные в другом формате, пробуем извлечь массив
        historyData = Object.values(response.data).find(Array.isArray) || [];
      }
      
      setHistory(historyData);
    } catch (error) {
      console.error('Ошибка загрузки истории:', error);
      setError('Не удалось загрузить историю игр');
      setHistory([]); // Устанавливаем пустой массив при ошибке
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Дата не указана';
    try {
      return new Date(dateString).toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  if (loading) {
    return <div className={styles.loading}>Загрузка истории игр...</div>;
  }

  return (
    <div className={styles.profileHistory}>
      <h1 className={styles.title}>История игр</h1>

      {error && (
        <div className={styles.error}>
          {error}
        </div>
      )}

      {!Array.isArray(history) || history.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🎮</div>
          <h3>История игр пуста</h3>
          <p>Сыграйте в свою первую викторину, чтобы увидеть здесь результаты!</p>
        </div>
      ) : (
        <div className={styles.historyList}>
          {history.map((game) => (
            <div key={game.id} className={styles.historyItem}>
              <div className={styles.gameHeader}>
                <h3 className={styles.quizTitle}>
                  {game.quiz_title || game.title || 'Викторина'}
                </h3>
                <div className={styles.gameRank}>
                  <span className={styles.rankIcon}>
                    {getRankIcon(game.final_rank || game.rank || 0)}
                  </span>
                </div>
              </div>

              <div className={styles.gameStats}>
                <div className={styles.stat}>
                  <span className={styles.statValue}>
                    {game.final_points || game.points || 0} очков
                  </span>
                  <span className={styles.statLabel}>Результат</span>
                </div>

                <div className={styles.stat}>
                  <span className={styles.statValue}>
                    {game.accuracy || (game.correct_answers && game.total_questions 
                      ? Math.round((game.correct_answers / game.total_questions) * 100)
                      : 0)}%
                  </span>
                  <span className={styles.statLabel}>Точность</span>
                </div>

                <div className={styles.stat}>
                  <span className={styles.statValue}>
                    {(game.correct_answers || 0)}/{(game.total_questions || 0)}
                  </span>
                  <span className={styles.statLabel}>Правильные ответы</span>
                </div>
              </div>

              <div className={styles.gameFooter}>
                <span className={styles.gameDate}>
                  {formatDate(game.played_at || game.created_at || game.date)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProfileHistory;