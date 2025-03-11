import {
  GcdsInput,
  GcdsSelect,
  GcdsButton,
  GcdsErrorMessage,
  GcdsText,
} from '@cdssnc/gcds-components-react';
import { useState, useEffect } from 'react';

const pt_codes = ['BC', 'ON'];
const pt_name_by_code = {
  BC: 'British Columbia',
  ON: 'Ontario',
};
const transfer_service_url_by_pt_code = {
  BC: process.env.BC_OUTBOUND_URL,
  ON: process.env.ON_OUTBOUND_URL,
};

const get_default_pt = () => {
  const default_pt_query_param = new URLSearchParams(
    window.location.search,
  ).get('default_pt');

  return pt_codes.includes(default_pt_query_param)
    ? default_pt_query_param
    : pt_codes[0];
};

const Form = () => {
  const default_pt = get_default_pt();
  const default_receiving_pt = pt_codes.find((pt) => pt !== default_pt);

  const [patientNumber, setPatientNumber] = useState('');
  const [originPT, setOriginPT] = useState(default_pt);
  const [receivingPT, setReceivingPT] = useState(default_receiving_pt);
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
        `${transfer_service_url_by_pt_code[originPT]}/transfer-request`,
      );

      if (!response.ok) throw new Error('Failed to load transfers');

      const data = await response.json();
      console.log(data);
      setTransfers(data); // Set the data to state
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

    try {
      const response = await fetch(
        `${transfer_service_url_by_pt_code[originPT]}/transfer-request`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            patient_id: patientNumber,
            transfer_to: receivingPT,
          }),
        },
      );

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
          onChange={(e) => {
            const new_origin_pt = e.target.value;

            if (receivingPT === new_origin_pt) {
              setReceivingPT(pt_codes.find((pt) => pt !== new_origin_pt));
            }
            setOriginPT(new_origin_pt);
          }}
        >
          {pt_codes.map((pt) => (
            <option value={pt} index={pt}>
              {pt_name_by_code[pt]}
            </option>
          ))}
        </GcdsSelect>
      </div>

      <div className="form-group">
        <GcdsSelect
          selectId="receivingPT"
          label="Receiving PT"
          name="receivingPT"
          hint="Select receiving PT."
          value={receivingPT}
          onChange={(e) => {
            const new_receiving_pt = e.target.value;

            if (originPT === new_receiving_pt) {
              setOriginPT(pt_codes.find((pt) => pt !== new_receiving_pt));
            }
            setReceivingPT(new_receiving_pt);
          }}
        >
          {pt_codes.map((pt) => (
            <option value={pt} index={pt}>
              {pt_name_by_code[pt]}
            </option>
          ))}
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
      )}
    </div>
  );
};

export default Form;
