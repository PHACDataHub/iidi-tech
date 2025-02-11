import './App.css';
import Home from './Pages/Home.jsx';
import Header from './Components/Header.jsx';
import Footer from './Components/Footer.jsx';
function App() {
  return (
    <>
      <header>
        <Header />
      </header>

      <main>
        <Home />
      </main>

      <footer>
        <Footer />
      </footer>
    </>
  );
}

export default App;