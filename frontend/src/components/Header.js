import React, { useState, useEffect, useRef } from 'react';
import styles from '../styles/Header.module.css';
import { Link, useNavigate } from 'react-router-dom';

const Header = () => {
  const [user, setUser] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setShowDropdown(false);
    navigate('/');
  };

  const handleProfileEdit = () => {
    setShowDropdown(false);
    navigate('/profile');
  };

  return (
    <header className={styles.header}>
      <nav className={styles.nav}>
        <Link to="/" className={styles.navLink}>Главная</Link>
        <Link to="/quizzes" className={styles.navLink}>Викторины</Link>
        <Link to="/rooms" className={styles.navLink}>Комнаты</Link>
        <Link to="/leaderboard" className={styles.navLink}>Лидеры</Link>

        {user ? (
          <div className={styles.userMenu} ref={dropdownRef}>
            <button
              className={styles.userButton}
              onClick={() => setShowDropdown(!showDropdown)}
            >
              👤 {user.nickname || user.email}
            </button>
            {showDropdown && (
              <div className={styles.dropdown}>
                <button
                  className={styles.dropdownItem}
                  onClick={handleProfileEdit}
                >
                  Изменить профиль
                </button>
                <button
                  className={styles.dropdownItem}
                  onClick={handleLogout}
                >
                  Выход из аккаунта
                </button>
              </div>
            )}
          </div>
        ) : (
          <Link to="/login" className={styles.navLink}>Войти</Link>
        )}
      </nav>
    </header>
  );
};

export default Header;