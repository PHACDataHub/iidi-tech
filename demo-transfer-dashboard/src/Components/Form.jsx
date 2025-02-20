import React, { useState } from 'react';
import {
  GcdsInput,
  GcdsText,
  GcdsButton,
  GcdsSelect,
  GcdsErrorMessage,
} from '@cdssnc/gcds-components-react';

const Form = () => {
  const [patientNumber, setPatientNumber] = useState('');
  const [originPT, setOriginPT] = useState('BC');
  const [receivingPT, setReceivingPT] = useState('ON');
  const [errorMessage, setErrorMessage] = useState('');
  const [loadingMessage, setLoadingMessage] = useState(false);
  const [transfers, setTransfers] = useState([]);

  const handlePatientNumberChange = (e) => {
    setPatientNumber(e.target.value);
  };

  const handleOriginPTChange = (e) => {
    setOriginPT(e.target.value);
  };

  const handleReceivingPTChange = (e) => {
    setReceivingPT(e.target.value);
  };

  const initiateTransfer = () => {
    setErrorMessage('');
    setLoadingMessage(true);

    // Validation checks
    if (!patientNumber.trim()) {
      setErrorMessage('Error: Patient Number is required.');
      setLoadingMessage(false);
      return;
    }

    if (originPT === receivingPT) {
      setErrorMessage('Error: Origin and Receiving PT cannot be the same.');
      setLoadingMessage(false);
      return;
    }

    // Simulating API Call
    const fhirUrl =
      originPT === 'BC'
        ? 'process.env.BC_OUTBOUND_URL'
        : 'process.env.ON_OUTBOUND_URL';
  };

  return (
    <div className="form-container">
      <div className="form-group">
        <GcdsInput
          inputId="patientNumber"
          label="Enter Patient Number"
          name="patientNumber"
          hint="Enter patient ID or name."
          value={patientNumber}
          onChange={handlePatientNumberChange}
        />
      </div>
      <div className="form-group">
        <GcdsSelect
          selectId="originPT"
          label="Originating PT"
          name="originPT"
          hint="Select originating PT."
          onChange={handleOriginPTChange}
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
          onChange={handleReceivingPTChange}
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
          <GcdsText>Processing transfer... Please wait.</GcdsText>
        </p>
      )}

      <table>
        <thead>
          <tr>
            <th>
              <GcdsText>Patient Name</GcdsText>
            </th>
            <th>
              <GcdsText>Origin PT</GcdsText>
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
              <td>{transfer.patientName}</td>
              <td>{transfer.originPT}</td>
              <td>{transfer.receivingPT}</td>
              <td
                className={`status ${transfer.status === 'Transferred' ? 'transferred' : 'failed'}`}
              >
                <GcdsText>{transfer.status}</GcdsText>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Form;
