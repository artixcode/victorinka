import Header from '../components/Header';
import Footer from '../components/Footer';

const Leaderboard = () => {
  return (
    <div>
      <Header />
      <main style={{ padding: '2rem', textAlign: 'center' }}>
        <h1>Таблица лидеров</h1>
        <p>Рейтинг игроков появится здесь скоро!</p>
      </main>
      <Footer />
    </div>
  );
};

export default Leaderboard;