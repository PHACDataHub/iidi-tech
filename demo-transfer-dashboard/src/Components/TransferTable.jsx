import { GcdsText, GcdsErrorMessage } from '@cdssnc/gcds-components-react';
import { useState, useEffect } from 'react';

import { transfer_service_url_by_pt_code } from 'src/pt_utils.js';

const TransferTable = ({ defaultPT }) => {
  const [transfers, setTransfers] = useState([]);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const transfer_service_url = transfer_service_url_by_pt_code[defaultPT];

  useEffect(() => {
    const fetchTransfers = async () => {
      try {
        setLoadingMessage('Loading transfer requests...');

        const response = await fetch(
          `${transfer_service_url}/transfer-request`,
        );

        if (!response.ok) throw new Error('Failed to load transfers');

        const data = await response.json();

        setTransfers(data);

        setLoadingMessage('');
      } catch (error) {
        console.log(error); // TODO delete console log, display relevant error information to user
        setErrorMessage('Failed to load transfer requests.');
        setLoadingMessage('');
      }
    };
    fetchTransfers();
  }, [transfer_service_url]);

  return (
    <>
      {errorMessage && (
        <p id="errorMessage" className="error">
          <GcdsErrorMessage messageId="message-props">
            {errorMessage}
          </GcdsErrorMessage>
        </p>
      )}
      {loadingMessage && (
        <p id="loadingMessage" className="loading">
          <GcdsText>{loadingMessage}</GcdsText>
        </p>
      )}
      <table style={{ marginTop: '50px' }}>
        <thead>
          <tr>
            <th>
              <GcdsText>Patient ID</GcdsText>
            </th>

            <th>
              <GcdsText>Receiving PT</GcdsText>
            </th>
            <th>
              <GcdsText>Transfer Status</GcdsText>
            </th>
            <th>
              <GcdsText>Transfer Stage </GcdsText>
            </th>
          </tr>
        </thead>
        <tbody>
          {transfers.map((transfer, index) => (
            <tr key={index}>
              <td>{transfer.patient_id}</td>
              <td>{transfer.transfer_to}</td>
              <td
                className={`status ${transfer.state === 'Completed' ? 'completed' : 'failed'}`}
              >
                <GcdsText>{transfer.state}</GcdsText>
              </td>
              <td>
                <GcdsText>{transfer.stage}</GcdsText>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
};

export default TransferTable;
