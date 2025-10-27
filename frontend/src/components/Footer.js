import React from 'react';
import { Link } from 'react-router-dom';
import styles from '../styles/Footer.module.css';

const Footer = () => {
  return (
    <footer className={styles.footer}>
      <div className={styles.footerContent}>
        <p className={styles.copyright}>&copy; Victorinka. Все права защищены.</p>
        <div className={styles.footerLinks}>
          <Link to="/about" className={styles.footerLink}>О проекте</Link>
          <Link to="/contact" className={styles.footerLink}>Контакты</Link>
          <Link to="/privacy" className={styles.footerLink}>Политика конфиденциальности</Link>
        </div>
      </div>
    </footer>
  );
};

export default Footer;