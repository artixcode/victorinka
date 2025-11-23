import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { authAPI } from '../services/authAPI';
import styles from '../styles/Profile.module.css';

const Profile = () => {
  const [user, setUser] = useState(null);
  const [formData, setFormData] = useState({
    nickname: '',
    email: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (!userData) {
      navigate('/login');
      return;
    }

    const userObj = JSON.parse(userData);
    setUser(userObj);
    setFormData({
      nickname: userObj.nickname || '',
      email: userObj.email || ''
    });
  }, [navigate]);

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
      const response = await authAPI.updateProfile(formData);
      const updatedUser = response.data;

      // Обновляем данные в localStorage
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);

      setMessage('Профиль успешно обновлен!');
    } catch (error) {
      console.error('Ошибка обновления профиля:', error);
      setMessage('Ошибка при обновлении профиля');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <div>Загрузка...</div>;
  }

  return (
    <div className={styles.pageContainer}>
      <Header />
      <div className={styles.profilePage}>
        <div className={styles.profileContainer}>
          <h1 className={styles.title}>Редактирование профиля</h1>

          {message && (
            <div className={message.includes('Ошибка') ? styles.error : styles.success}>
              {message}
            </div>
          )}

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
                placeholder="Введите ваш email"
                required
                disabled={loading}
              />
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
      <Footer />
    </div>
  );
};

export default Profile;