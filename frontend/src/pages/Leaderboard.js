import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import styles from '../styles/Leaderboard.module.css';
import leaderboardAPI from '../services/leaderboardAPI';
import Header from '../components/Header';
import Footer from '../components/Footer';

const Leaderboard = () => {
  const [activeTab, setActiveTab] = useState('global');
  const [leaderboardData, setLeaderboardData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [quizId, setQuizId] = useState('');
  const [ordering, setOrdering] = useState('-total_points');

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      let data;
      if (activeTab === 'global') {
        data = await leaderboardAPI.fetchGlobalLeaderboard(ordering);
      } else if (activeTab === 'quiz' && quizId) {
        data = await leaderboardAPI.fetchQuizLeaderboard(quizId);
      }

      if (data && typeof data === 'object' && !Array.isArray(data)) {
        if (data.leaderboard && Array.isArray(data.leaderboard)) {
          data = data.leaderboard;
        } else if (Array.isArray(data.results)) {
          data = data.results;
        } else {
          data = Object.values(data);
        }
      }

      setLeaderboardData(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setLeaderboardData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, ordering, quizId]);

  const handleQuizSubmit = (e) => {
    e.preventDefault();
    if (quizId.trim()) {
      fetchData();
    }
  };

  const getRankColor = (rank) => {
    return leaderboardAPI.getRankColor(rank);
  };

  const getPlayerLevel = (points) => {
    return leaderboardAPI.getPlayerLevel(points);
  };

  const formatRank = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return rank;
  };

  const renderLeaderboardRows = () => {
    if (!Array.isArray(leaderboardData)) {
      return null;
    }

    return leaderboardData.map((player, index) => {
      const rank = player.rank || index + 1;
      const playerLevel = getPlayerLevel(player.total_points || player.best_score || 0);
      const accuracy = player.avg_accuracy ||
        leaderboardAPI.calculateAccuracy(
          player.correct_answers || 0,
          player.total_questions || 0
        );

      return (
        <div key={player.id || player.user_id || index} className={styles.leaderboardRow}>
          <div className={styles.rankCell}>
            <span
              className={styles.rankBadge}
              style={{ background: getRankColor(rank) }}
            >
              {formatRank(rank)}
            </span>
          </div>

          <div className={styles.playerCell}>
            <div className={styles.playerInfo}>
              <div className={styles.playerName}>
                {player.nickname || `Игрок #${player.user_id || index}`}
              </div>
              <div className={styles.playerMeta}>
                {playerLevel && (
                  <span
                    className={styles.levelBadge}
                    style={{
                      background: `${playerLevel.color}20`,
                      color: playerLevel.color,
                      borderColor: playerLevel.color
                    }}
                  >
                    {playerLevel.level}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className={styles.statCell}>
            <span className={styles.statValue}>
              {player.total_points || player.best_score || 0}
            </span>
          </div>

          <div className={styles.statCell}>
            <span className={styles.statValue}>
              {player.total_wins || 0}
            </span>
          </div>

          <div className={styles.statCell}>
            <span className={styles.statValue}>
              {player.total_games || player.games_played || 0}
            </span>
          </div>

          <div className={styles.statCell}>
            <div className={styles.accuracyCell}>
              <span className={styles.accuracyValue}>
                {accuracy}%
              </span>
              <div className={styles.accuracyBar}>
                <div
                  className={styles.accuracyFill}
                  style={{ width: `${Math.min(accuracy, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      );
    });
  };

  return (
    <div className={styles.pageContainer}>
      <Header />
      <main className={styles.main}>
        <div className={styles.heroSection}>
          <h1 className={styles.title}>🏆 Таблица лидеров</h1>
          <p className={styles.subtitle}>Следите за лучшими игроками и соревнуйтесь за первые места</p>
        </div>

        <div className={styles.controls}>
          <div className={styles.tabs}>
            <button
              className={`${styles.tab} ${activeTab === 'global' ? styles.active : ''}`}
              onClick={() => setActiveTab('global')}
            >
              Глобальный рейтинг
            </button>
            <button
              className={`${styles.tab} ${activeTab === 'quiz' ? styles.active : ''}`}
              onClick={() => setActiveTab('quiz')}
            >
              Рейтинг по викторине
            </button>
          </div>

          {activeTab === 'global' && (
            <div className={styles.sortControls}>
              <label>Сортировка:</label>
              <select
                className={styles.sortSelect}
                value={ordering}
                onChange={(e) => setOrdering(e.target.value)}
              >
                <option value="-total_points">По очкам (убывание)</option>
                <option value="total_points">По очкам (возрастание)</option>
                <option value="-total_wins">По победам</option>
                <option value="nickname">По имени (А-Я)</option>
                <option value="-nickname">По имени (Я-А)</option>
              </select>
            </div>
          )}

          {activeTab === 'quiz' && (
            <form className={styles.quizForm} onSubmit={handleQuizSubmit}>
              <input
                type="text"
                className={styles.quizInput}
                placeholder="Введите ID викторины"
                value={quizId}
                onChange={(e) => setQuizId(e.target.value)}
              />
              <button type="submit" className={styles.searchButton}>
                Показать рейтинг
              </button>
            </form>
          )}
        </div>

        <div className={styles.content}>
          {loading ? (
            <div className={styles.loading}>
              <div className={styles.spinner}></div>
              <p>Загрузка рейтинга...</p>
            </div>
          ) : error ? (
            <div className={styles.error}>
              <p>{error}</p>
              <button onClick={fetchData} className={styles.retryButton}>
                Попробовать снова
              </button>
            </div>
          ) : !Array.isArray(leaderboardData) || leaderboardData.length === 0 ? (
            <div className={styles.emptyState}>
              {activeTab === 'quiz' && !quizId ? (
                <>
                  <p>Введите ID викторины для просмотра рейтинга</p>
                  <Link to="/quizzes" className={styles.browseLink}>
                    Посмотреть все викторины →
                  </Link>
                </>
              ) : (
                <>
                  <p>Нет данных для отображения</p>
                  <p className={styles.emptySubtitle}>Будьте первым, кто попадет в таблицу лидеров!</p>
                </>
              )}
            </div>
          ) : (
            <div className={styles.leaderboardContainer}>
              <div className={styles.tableHeader}>
                <div className={styles.rankHeader}>Место</div>
                <div className={styles.playerHeader}>Игрок</div>
                <div className={styles.statsHeader}>Очки</div>
                <div className={styles.statsHeader}>Победы</div>
                <div className={styles.statsHeader}>Игры</div>
                <div className={styles.statsHeader}>Точность</div>
              </div>

              <div className={styles.leaderboardList}>
                {renderLeaderboardRows()}
              </div>
            </div>
          )}
        </div>

        <div className={styles.actions}>
          <Link to="/quizzes" className={styles.actionButton}>
            ← К викторинам
          </Link>
          <Link to="/create-room" className={styles.actionButton}>
            Создать комнату
          </Link>
          <Link to="/profile" className={styles.actionButtonPrimary}>
            Мой профиль
          </Link>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Leaderboard;