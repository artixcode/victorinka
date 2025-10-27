import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { authAPI } from '../services/authAPI';
import styles from '../styles/Login.module.css';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
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

    try {
      // Вызов твоего JWT login эндпоинта
      const response = await authAPI.login(formData.email, formData.password);

      // Сохраняем JWT токены
      const { access, refresh } = response.data;

      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      // Получаем данные пользователя
      const profileResponse = await authAPI.getProfile();
      const user = profileResponse.data;

      localStorage.setItem('user', JSON.stringify(user));

      console.log('Успешный вход:', user);
      alert(`Добро пожаловать, ${user.full_name || user.email}!`);

      // Перенаправляем на главную
      navigate('/');

    } catch (error) {
      console.error('Ошибка входа:', error);
      setError(
        error.response?.data?.detail ||
        error.response?.data?.error ||
        'Неверный email или пароль'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.pageContainer}>
      <Header />

      <div className={styles.loginPage}>
        <div className={styles.loginContainer}>
          <h1 className={styles.title}>Вход в Victorinka</h1>

          {error && (
            <div className={styles.error}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.loginForm}>
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
              <label htmlFor="password" className={styles.label}>Пароль</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={styles.input}
                placeholder="Введите пароль"
                required
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              className={styles.loginButton}
              disabled={loading}
            >
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>

          <div className={styles.links}>
            <Link to="/register" className={styles.link}>Зарегистрироваться</Link>
            <Link to="/forgot-password" className={styles.link}>Забыли пароль?</Link>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Login;