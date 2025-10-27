import Header from '../components/Header';
import Footer from '../components/Footer';

const Home = () => {
    //console.log('Home component is rendering!');
  return (
    <div>
      <Header />
      <main>Контент главной страницы</main>
      <Footer />
    </div>
  );
};

export default Home;