import React from 'react';
import styles from '../styles/Header.module.css';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="header">
      <nav className={styles.header}>
          <Link to="/" className={styles.navLink}>Главная</Link>
          <Link to="/" className={styles.navLink}>Викторины</Link>
          <Link to="/" className={styles.navLink}>Создать комнату</Link>
          <Link to="/" className={styles.navLink}>Создать вопросы</Link>
          <Link to="/" className={styles.navLink}>Лидеры</Link>
          <Link to="/login" className={styles.navLink}>Войти</Link>
      </nav>
    </header>
  );
};

export default Header;