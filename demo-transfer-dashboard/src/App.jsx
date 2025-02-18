import './App.css';
import Header from './Components/Header.jsx';
import Footer from './Components/Footer.jsx';
import { useEffect } from 'react';

function App() {
  useEffect(() => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href =
      'https://www.canada.ca/etc/designs/canada/cdts/gcweb/v4_0_32/css/theme.min.css';
    document.head.appendChild(link);
  }, []);

  return (
    <>
      <Header language="en" textColor="black" flagColor="#EA2D37" />

      <main>
        <section className="alert alert-info">
          <h3>This is a work in progress.</h3>
          <p>Information may be incorrect or inaccurate.</p>
        </section>
        <h1>Home Page</h1>
        <p>This is the content of the Home page.</p>
      </main>

      <footer>
        <Footer />
      </footer>
    </>
  );
}

export default App;
