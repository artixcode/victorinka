import React, { useState, useEffect } from 'react';
import { authAPI } from '../services/authAPI';
import { cabinetAPI } from '../services/cabinetAPI';
import styles from '../styles/ProfileInfo.module.css';

const ProfileInfo = () => {
  const [user, setUser] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [formData, setFormData] = useState({
    nickname: '',
    email: ''
  });
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      const userObj = JSON.parse(userData);
      setUser(userObj);
      setFormData({
        nickname: userObj.nickname || '',
        email: userObj.email || ''
      });
      loadUserStats();
    }
  }, []);

  const loadUserStats = async () => {
    try {
      setStatsLoading(true);
      const statsResponse = await cabinetAPI.getStats();
      console.log('Stats API response:', statsResponse); // Для отладки

      let statsData = {};
      if (typeof statsResponse.data === 'object' && statsResponse.data !== null) {
        statsData = statsResponse.data;
      }

      setUserStats(statsData);
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
      const userData = JSON.parse(localStorage.getItem('user'));
      setUserStats({
        total_points: userData?.total_points || 0,
        total_wins: userData?.total_wins || 0,
        total_games: 0,
        correct_answers: 0,
        total_answers: 0,
        avg_accuracy: 0
      });
    } finally {
      setStatsLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await authAPI.updateProfile({ nickname: formData.nickname });
      const updatedUser = response.data;

      const currentUser = JSON.parse(localStorage.getItem('user'));
      const mergedUser = { ...currentUser, ...updatedUser };
      localStorage.setItem('user', JSON.stringify(mergedUser));
      setUser(mergedUser);

      setMessage('Профиль успешно обновлен!');
    } catch (error) {
      console.error('Ошибка обновления профиля:', error);
      setMessage(
        error.response?.data?.nickname?.[0] ||
        error.response?.data?.detail ||
        'Ошибка при обновлении профиля'
      );
    } finally {
      setLoading(false);
    }
  };

  const calculateWinRate = () => {
    if (!userStats || !userStats.total_games || userStats.total_games === 0) return 0;
    return Math.round((userStats.total_wins / userStats.total_games) * 100);
  };

  const calculateAccuracy = () => {
    if (!userStats || !userStats.total_answers || userStats.total_answers === 0) return 0;
    return Math.round((userStats.correct_answers / userStats.total_answers) * 100);
  };

  if (!user) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  return (
    <div className={styles.profileInfo}>
      <h1 className={styles.title}>Личные данные</h1>

      {message && (
        <div className={message.includes('Ошибка') ? styles.error : styles.success}>
          {message}
        </div>
      )}

      {/* Статистика */}
      <div className={styles.statsSection}>
        <h2 className={styles.sectionTitle}>Ваша статистика</h2>

        {statsLoading ? (
          <div className={styles.loading}>Загрузка статистики...</div>
        ) : userStats ? (
          <div className={styles.statsGrid}>
            <div className={styles.statCard}>
              <div className={styles.statValue}>{userStats.total_points || 0}</div>
              <div className={styles.statLabel}>Всего очков</div>
            </div>

            <div className={styles.statCard}>
              <div className={styles.statValue}>{userStats.total_wins || 0}</div>
              <div className={styles.statLabel}>Побед</div>
            </div>

            {userStats.total_games !== undefined && (
              <div className={styles.statCard}>
                <div className={styles.statValue}>{userStats.total_games}</div>
                <div className={styles.statLabel}>Всего игр</div>
              </div>
            )}

            {userStats.total_games !== undefined && userStats.total_games > 0 && (
              <div className={styles.statCard}>
                <div className={styles.statValue}>{calculateWinRate()}%</div>
                <div className={styles.statLabel}>Процент побед</div>
              </div>
            )}

            {(userStats.avg_accuracy !== undefined || userStats.correct_answers !== undefined) && (
              <div className={styles.statCard}>
                <div className={styles.statValue}>
                  {userStats.avg_accuracy ? userStats.avg_accuracy + '%' : calculateAccuracy() + '%'}
                </div>
                <div className={styles.statLabel}>Точность</div>
              </div>
            )}

            {/* Дополнительные поля статистики */}
            {userStats.correct_answers !== undefined && (
              <div className={styles.statCard}>
                <div className={styles.statValue}>{userStats.correct_answers}</div>
                <div className={styles.statLabel}>Правильных ответов</div>
              </div>
            )}

            {userStats.bookmarks_count !== undefined && (
              <div className={styles.statCard}>
                <div className={styles.statValue}>{userStats.bookmarks_count}</div>
                <div className={styles.statLabel}>Закладок</div>
              </div>
            )}

            {userStats.active_rooms_count !== undefined && (
              <div className={styles.statCard}>
                <div className={styles.statValue}>{userStats.active_rooms_count}</div>
                <div className={styles.statLabel}>Активных комнат</div>
              </div>
            )}

            {userStats.global_rank !== undefined && (
              <div className={`${styles.statCard} ${styles.rankCard}`}>
                <div className={styles.statValue}>
                  {userStats.global_rank <= 3 ? (
                    <>
                      {userStats.global_rank === 1 && '🥇'}
                      {userStats.global_rank === 2 && '🥈'}
                      {userStats.global_rank === 3 && '🥉'}
                    </>
                  ) : (
                    `#${userStats.global_rank}`
                  )}
                </div>
                <div className={styles.statLabel}>Место в рейтинге</div>
              </div>
            )}
          </div>
        ) : (
          <div className={styles.error}>Не удалось загрузить статистику</div>
        )}
      </div>

      {/* Форма редактирования */}
      <div className={styles.editSection}>
        <h2 className={styles.sectionTitle}>Редактирование профиля</h2>

        <form onSubmit={handleSubmit} className={styles.profileForm}>
          <div className={styles.formGroup}>
            <label htmlFor="nickname" className={styles.label}>Никнейм</label>
            <input
              type="text"
              id="nickname"
              name="nickname"
              value={formData.nickname}
              onChange={handleChange}
              className={styles.input}
              placeholder="Введите ваш никнейм"
              required
              disabled={loading}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="email" className={styles.label}>Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className={styles.input}
              disabled
              title="Email нельзя изменить"
            />
            <small className={styles.helpText}>Email нельзя изменить</small>
          </div>

          <button
            type="submit"
            className={styles.saveButton}
            disabled={loading}
          >
            {loading ? 'Сохранение...' : 'Сохранить изменения'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ProfileInfo;