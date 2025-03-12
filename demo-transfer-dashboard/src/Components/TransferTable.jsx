import './TransferTable.css';

import {
  GcdsText,
  GcdsNotice,
  GcdsButton,
  GcdsHeading,
} from '@cdssnc/gcds-components-react';
import { useState, useEffect } from 'react';

import {
  transfer_service_url_by_pt_code,
  pt_name_by_code,
} from 'src/pt_utils.js';

const TransferTableHeader = ({ children }) => (
  <th>
    <GcdsText>
      <div className="transfer-table__table-header">{children}</div>
    </GcdsText>
  </th>
);

const TransferTableData = ({ children }) => (
  <td>
    <GcdsText>
      <div className="transfer-table__table-data">{children}</div>
    </GcdsText>
  </td>
);

const TransferTable = ({ outboundPT }) => {
  const transfer_service_url = transfer_service_url_by_pt_code[outboundPT];

  const [loading, setLoading] = useState(true);
  const [showLoading, setShowLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [transfers, setTransfers] = useState([]);
  const [lastRefresh, setlastRefresh] = useState();

  useEffect(() => {
    const fetchTransfers = async () => {
      if (loading) {
        try {
          const response = await fetch(
            `${transfer_service_url}/transfer-request`,
          );

          const data = await response.json().catch(() => null);

          if (!response.ok) {
            throw new Error(
              `Failed to get info on transfers: ${'error' in data ? data.error : response.statusText}`,
            );
          } else {
            if (data) {
              setTransfers(data);
            } else {
              throw new Error(
                'Transfer service did not respond with expected data, please contact a developer.',
              );
            }
          }
        } catch (error) {
          setErrorMessage(error.toString());
        } finally {
          setlastRefresh(
            new Intl.DateTimeFormat('en-CA', {
              dateStyle: 'short',
              timeStyle: 'long',
            }).format(),
          );
          setLoading(false);
        }
      }
    };
    fetchTransfers();
  }, [transfer_service_url, loading]);

  useEffect(() => {
    if (!loading) {
      setShowLoading(false);
    } else {
      const handler = setTimeout(() => {
        setShowLoading(true);
      }, 200);
      return () => {
        clearTimeout(handler);
      };
    }
  }, [loading]);

  const get_transfer_row_class_modifier = ({ state, stage }) => {
    if ((state === 'completed' && stage === 'rejected') || state === 'failed') {
      return 'failed';
    } else if (state === 'completed' && stage === 'done') {
      return 'succeeded';
    } else {
      return 'ongoing';
    }
  };

  const get_transfer_status_text = (transfer) => 'TODO';

  return (
    <>
      <div className="transfer-table-header">
        <GcdsHeading tag="h2">Transfer Requests</GcdsHeading>
        <GcdsButton disabled={showLoading} onClick={() => setLoading(true)}>
          <div style={{ width: '125px' }}>
            {!showLoading ? 'Refresh' : 'Loading...'}
          </div>
        </GcdsButton>
      </div>

      {errorMessage && (
        <div style={{ paddingTop: '20px' }}>
          <GcdsNotice type={'danger'} noticeTitleTag="h3" noticeTitle={'Error'}>
            <GcdsText>{errorMessage}</GcdsText>
          </GcdsNotice>
        </div>
      )}
      <div style={{ overflowX: 'auto' }}>
        <table className="transfer-table">
          <caption align="bottom">
            <GcdsText size="small">
              Summary of {pt_name_by_code[outboundPT]}'s historical and ongoing
              patient transfers.
              <br></br>
              {lastRefresh
                ? `Last refreshed: ${lastRefresh}`
                : 'Loading initial data...'}
            </GcdsText>
          </caption>
          <thead>
            <tr>
              <TransferTableHeader>Transfer Job ID</TransferTableHeader>
              <TransferTableHeader>Patient ID</TransferTableHeader>
              <TransferTableHeader>Receiving PT</TransferTableHeader>
              <TransferTableHeader>Transfer Status</TransferTableHeader>
            </tr>
          </thead>
          <tbody>
            {transfers.map((transfer) => (
              <tr
                key={transfer.job_id}
                className={`transfer-table__row transfer-table__row--${get_transfer_row_class_modifier(transfer)}`}
              >
                <TransferTableData>{transfer.job_id}</TransferTableData>
                <TransferTableData>{transfer.patient_id}</TransferTableData>
                <TransferTableData>
                  {pt_name_by_code[transfer.transfer_to]}
                </TransferTableData>
                <TransferTableData>
                  {get_transfer_status_text(transfer)}
                </TransferTableData>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!loading && transfers.length === 0 && (
        <div
          style={{
            paddingTop: '20px',
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <GcdsNotice type={'info'} noticeTitleTag="h4" noticeTitle={'No Data'}>
            <GcdsText>No transfer requests were found</GcdsText>
          </GcdsNotice>
        </div>
      )}
    </>
  );
};

export default TransferTable;
