import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { authAPI } from '../services/authAPI';
import styles from '../styles/Register.module.css';

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    nickname: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: value
    }));
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Валидация паролей
    if (formData.password !== formData.confirmPassword) {
      setError('Пароли не совпадают');
      setLoading(false);
      return;
    }

    if (formData.password.length < 8) {
      setError('Пароль должен содержать минимум 8 символов');
      setLoading(false);
      return;
    }

    try {
      // Отправляем данные для регистрации
      const response = await authAPI.register({
        email: formData.email,
        nickname: formData.nickname,
        password: formData.password
      });

      console.log('Успешная регистрация:', response.data);

      // Автоматически логиним пользователя после регистрации
      const loginResponse = await authAPI.login(formData.email, formData.password);
      const { access, refresh } = loginResponse.data;

      // Сохраняем токены
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      // Получаем профиль
      const profileResponse = await authAPI.getProfile();
      const user = profileResponse.data;
      localStorage.setItem('user', JSON.stringify(user));

      alert(`Добро пожаловать, ${user.nickname || user.email}!`);
      navigate('/');

    } catch (error) {
      console.error('Ошибка регистрации:', error);
      setError(
        error.response?.data?.email?.[0] ||
        error.response?.data?.nickname?.[0] ||
        error.response?.data?.password?.[0] ||
        error.response?.data?.detail ||
        'Ошибка при регистрации'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.pageContainer}>
      <Header />

      <div className={styles.registerPage}>
        <div className={styles.registerContainer}>
          <h1 className={styles.title}>Регистрация в Victorinka</h1>

          {error && (
            <div className={styles.error}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.registerForm}>
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

            <div className={styles.formGroup}>
              <label htmlFor="nickname" className={styles.label}>Никнейм</label>
              <input
                type="text"
                id="nickname"
                name="nickname"
                value={formData.nickname}
                onChange={handleChange}
                className={styles.input}
                placeholder="Придумайте никнейм"
                required
                disabled={loading}
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="password" className={styles.label}>Пароль</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={styles.input}
                placeholder="Придумайте пароль (мин. 8 символов)"
                required
                minLength="8"
                disabled={loading}
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="confirmPassword" className={styles.label}>Подтвердите пароль</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className={styles.input}
                placeholder="Повторите пароль"
                required
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              className={styles.registerButton}
              disabled={loading}
            >
              {loading ? 'Регистрация...' : 'Зарегистрироваться'}
            </button>
          </form>

          <div className={styles.links}>
            <Link to="/login" className={styles.link}>Уже есть аккаунт? Войти</Link>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Register;