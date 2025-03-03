import { useState, useEffect } from 'react';
import {
  GcdsInput,
  GcdsSelect,
  GcdsButton,
  GcdsErrorMessage,
  GcdsText,
} from '@cdssnc/gcds-components-react';

const Form = () => {
  const [patientNumber, setPatientNumber] = useState('');
  const [originPT, setOriginPT] = useState('BC');
  const [receivingPT, setReceivingPT] = useState('ON');
  const [transfers, setTransfers] = useState([]);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    fetchTransfers();
  }, []);

  // Logic work in progress
  const fetchTransfers = async () => {
    try {
      setLoadingMessage('Loading transfer requests...');
      const response = await fetch(
        `${process.env.BC_OUTBOUND_URL}/transfer-request`,
      );
      if (!response.ok) throw new Error('Failed to load transfers');

      const data = await response.json();
      console.log(data);
      setTransfers(data);
      setLoadingMessage('');
    } catch (error) {
      setErrorMessage('Failed to load transfer requests.');
      setLoadingMessage('');
    }
  };

  const initiateTransfer = async () => {
    setErrorMessage('');
    if (!patientNumber.trim()) {
      setErrorMessage('Please enter a valid patient number.');
      return;
    }

    setLoadingMessage('Processing transfer... Please wait.');

    const fhirUrl =
      originPT === 'BC'
        ? process.env.BC_OUTBOUND_URL
        : process.env.ON_OUTBOUND_URL;

    try {
      const response = await fetch(`${fhirUrl}/transfer-request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientNumber,
          transfer_to: receivingPT,
        }),
      });

      if (!response.ok) throw new Error('Failed to initiate transfer');

      const data = await response.json();
      setTransfers((prevTransfers) => [...prevTransfers, data]);
      setLoadingMessage('');
    } catch (error) {
      setErrorMessage('Transfer request failed. Please try again.');
      setLoadingMessage('');
    }
  };

  return (
    <div className="form-container">
      <div className="form-group">
        <GcdsInput label="Enter Patient First Name" hint="Enter First name." />
      </div>
      <div className="form-group">
        <GcdsInput label="Enter Patient Last Name" hint="Enter Last name." />
      </div>
      <div className="form-group">
        <GcdsInput
          inputId="patientNumber"
          label="Enter Patient Number"
          name="patientNumber"
          hint="Enter patient ID."
          value={patientNumber}
          onChange={(e) => setPatientNumber(e.target.value)}
        />
      </div>

      <div className="form-group">
        <GcdsSelect
          selectId="originPT"
          label="Originating PT"
          name="originPT"
          hint="Select originating PT."
          value={originPT}
          onChange={(e) => setOriginPT(e.target.value)}
        >
          <option value="BC">British Columbia</option>
          <option value="ON">Ontario</option>
        </GcdsSelect>
      </div>

      <div className="form-group">
        <GcdsSelect
          selectId="receivingPT"
          label="Receiving PT"
          name="receivingPT"
          hint="Select receiving PT."
          value={receivingPT}
          onChange={(e) => setReceivingPT(e.target.value)}
        >
          <option value="ON">Ontario</option>
          <option value="BC">British Columbia</option>
        </GcdsSelect>
      </div>

      <GcdsButton onClick={initiateTransfer}>Initiate Transfer</GcdsButton>

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

      {transfers.length > 0 && (
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
            </tr>
          </thead>
          <tbody>
            {transfers.map((transfer, index) => (
              <tr key={index}>
                <td>{transfer.patient_id}</td>
                <td>{transfer.transfer_to}</td>
                <td
                  className={`status ${transfer.status === 'Transferred' ? 'transferred' : 'failed'}`}
                >
                  <GcdsText>{transfer.state}</GcdsText>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default Form;
