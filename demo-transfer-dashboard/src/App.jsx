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

import { get_outbound_pt, pt_name_by_code } from './pt_utils.js';

function App() {
  const outbound_pt = get_outbound_pt();

  return (
    <>
      <header>
        <GcdsHeader />
      </header>

      <main>
        <WorkInProgressAlert />

        <GcdsHeading tag="h1">
          PT-to-PT MMR Immunization Record Transfer:{' '}
          {pt_name_by_code[outbound_pt]}
        </GcdsHeading>

        <TransferForm outboundPT={outbound_pt} />

        <TransferTable outboundPT={outbound_pt} />

        <GcdsDateModified> {process.env.BUILD_DATE}</GcdsDateModified>
      </main>

      <footer>
        <GcdsFooter />
      </footer>
    </>
  );
}

export default App;
