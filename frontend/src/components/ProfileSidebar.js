// components/ProfileSidebar.js
import React from 'react';
import styles from '../styles/ProfileSidebar.module.css';

const ProfileSidebar = ({ activeSection, onSectionChange }) => {
  const menuItems = [
    { key: 'info', label: 'Личные данные', icon: '👤' },
    { key: 'history', label: 'История игр', icon: '📊' },
    { key: 'bookmarks', label: 'Закладки', icon: '🔖' }
  ];

  return (
    <div className={styles.sidebar}>
      <div className={styles.sidebarHeader}>
        <h2 className={styles.sidebarTitle}>Личный кабинет</h2>
      </div>

      <nav className={styles.sidebarNav}>
        {menuItems.map(item => (
          <button
            key={item.key}
            className={`${styles.navItem} ${activeSection === item.key ? styles.navItemActive : ''}`}
            onClick={() => onSectionChange(item.key)}
            type="button"
          >
            <span className={styles.navIcon}>{item.icon}</span>
            <span className={styles.navLabel}>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className={styles.sidebarFooter}>
        <div className={styles.userInfo}>
          <span className={styles.userWelcome}>Добро пожаловать!</span>
        </div>
      </div>
    </div>
  );
};

export default ProfileSidebar;