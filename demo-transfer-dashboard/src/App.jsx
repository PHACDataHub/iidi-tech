import './App.css';
import Header from './Components/Header.jsx';
import Footer from './Components/Footer.jsx';
import Form from './Components/Form.jsx';
import { GcdsDateModified, GcdsHeading } from '@cdssnc/gcds-components-react';
import Alert from './Components/Alert.jsx';


function App() {
  return (
    <>
      <Header language="en" textColor="black" flagColor="#EA2D37" />

      <main>
        <section className="alert alert-info">
          
            <Alert/>
         
        </section>
        <GcdsHeading tag="h1">PT-to-PT MMR Immunization Record Transfer</GcdsHeading>
        <Form />
        <GcdsDateModified>
          2025-02-19
        </GcdsDateModified>
      </main>

      <footer>
        <Footer />
      </footer>
    </>
  );
}

export default App;
