// Home.js
import Header from '../components/Header';
import Footer from '../components/Footer';
import { Link } from 'react-router-dom';
import styles from '../styles/Home.module.css';

const Home = () => {
  return (
    <div className={styles.pageContainer}>
      <Header />
      <main className={styles.main}>
        <section className={styles.hero}>
          <h1>Добро пожаловать в Victorinka!</h1>
          <p>Проверяйте свои знания, создавайте свои викторины и соревнуйтесь с друзьями.</p>
          <div className={styles.ctaContainer}>
            <Link to="/quizzes" className={`${styles.ctaButton} ${styles.primary}`}>Начать викторину</Link>
            <Link to="/leaderboard" className={styles.ctaButton}>Таблица лидеров</Link>
          </div>
        </section>

        <section className={styles.features}>
          <div className={styles.featureCard}>
            <h3>Участвуйте в викторинах</h3>
            <p>Ответьте на вопросы из различных категорий и тем.</p>
            <Link to="/quizzes" className={styles.featureLink}>Смотреть викторины →</Link>
          </div>
          <div className={styles.featureCard}>
            <h3>Соревнуйтесь!</h3>
            <p>Займите верхнюю строчку в рейтинге самых умных.</p>
            <Link to="/leaderboard" className={styles.featureLink}>К лидерам →</Link>
          </div>
          <div className={styles.featureCard}>
            <h3>Создайте комнату!</h3>
            <p>Пригласите друзей и сыграйте вместе в режиме реального времени.</p>
            <Link to="/create-room" className={styles.featureLink}>Создать комнату →</Link>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Home;