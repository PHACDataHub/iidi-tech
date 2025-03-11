import './App.css';
import {
  GcdsDateModified,
  GcdsHeading,
  GcdsFooter,
  GcdsHeader,
} from '@cdssnc/gcds-components-react';

import TransferForm from './Components/TransferForm.jsx';
import TransferTable from './Components/TransferTable.jsx';
import WorkInProgressAlert from './Components/WorkInProgressAlert.jsx';

import { get_default_pt } from './pt_utils.js';

function App() {
  const default_pt = get_default_pt();

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
        <TransferForm defaultPT={default_pt} />
        <TransferTable defaultPT={default_pt} />
        <GcdsDateModified> {process.env.BUILD_DATE}</GcdsDateModified>
      </main>

      <footer>
        <GcdsFooter />
      </footer>
    </>
  );
}

export default App;
