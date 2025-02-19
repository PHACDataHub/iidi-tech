import './App.css';
import Form from './Components/Form.jsx';
import {
  GcdsDateModified,
  GcdsHeading,
  GcdsFooter,
  GcdsHeader,
} from '@cdssnc/gcds-components-react';
import Alert from './Components/Alert.jsx';

function App() {
  return (
    <>
      <header>
        <GcdsHeader />
      </header>

      <main>
        <Alert />

        <GcdsHeading tag="h1">
          PT-to-PT MMR Immunization Record Transfer
        </GcdsHeading>
        <Form />
        <GcdsDateModified>2025-02-19</GcdsDateModified>
      </main>

      <footer>
        <GcdsFooter />
      </footer>
    </>
  );
}

export default App;
