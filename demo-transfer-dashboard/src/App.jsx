import './App.css';
import {
  GcdsDateModified,
  GcdsHeading,
  GcdsFooter,
  GcdsHeader,
} from '@cdssnc/gcds-components-react';

import Form from './Components/Form.jsx';
import WorkInProgressAlert from './Components/WorkInProgressAlert.jsx';

function App() {
  return (
    <>
      <header>
        <GcdsHeader />
      </header>

      <main>
        <WorkInProgressAlert />

        <GcdsHeading tag="h1">
          PT-to-PT MMR Immunization Record Transfer
        </GcdsHeading>
        <Form />
        <GcdsDateModified> {process.env.BUILD_DATE}</GcdsDateModified>
      </main>

      <footer>
        <GcdsFooter />
      </footer>
    </>
  );
}

export default App;
