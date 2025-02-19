import React, { useState } from 'react';

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
    const fhirUrl = originPT === 'BC' 
      ? "https://fhir.bc.iidi.alpha.phac.gc.ca/" 
      : "https://fhir.on.iidi.alpha.phac.gc.ca/";

    const payload = {
      resourceType: "Immunization",
      patient: { reference: `Patient/${patientNumber}` },
      vaccineCode: {
        coding: [{ system: "http://hl7.org/fhir/sid/cvx", code: "03", display: "MMR" }]
      },
      occurrenceDateTime: new Date().toISOString(),
      status: "completed"
    };

    fetch(fhirUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((response) => response.json())
      .then((data) => {
        setLoadingMessage(false);
        const status = data.resourceType === "OperationOutcome" ? "Failed" : "Transferred";
        addToTable(patientNumber, originPT, receivingPT, status);
      })
      .catch((error) => {
        setLoadingMessage(false);
        addToTable(patientNumber, originPT, receivingPT, "Failed");
      });
  };

  const addToTable = (patientName, originPT, receivingPT, status) => {
    setTransfers((prevTransfers) => [
      ...prevTransfers,
      { patientName, originPT, receivingPT, vaccine: 'MMR', status },
    ]);
  };

  return (
    <div className="container">
      <div className="form-group">
        <label htmlFor="patientNumber">Enter Patient Number:</label>
        <input
          type="text"
          id="patientNumber"
          value={patientNumber}
          onChange={handlePatientNumberChange}
          placeholder="Enter patient ID or name"
        />
      </div>
      <div className="form-group">
        <label htmlFor="originPT">Originating PT:</label>
        <select id="originPT" value={originPT} onChange={handleOriginPTChange}>
          <option value="BC">British Columbia</option>
          <option value="ON">Ontario</option>
        </select>
      </div>
      <div className="form-group">
        <label htmlFor="receivingPT">Receiving PT:</label>
        <select id="receivingPT" value={receivingPT} onChange={handleReceivingPTChange}>
          <option value="ON">Ontario</option>
          <option value="BC">British Columbia</option>
        </select>
      </div>
      <button onClick={initiateTransfer}>Initiate Transfer</button>
      {errorMessage && <p id="errorMessage" className="error">{errorMessage}</p>}
      {loadingMessage && <p id="loadingMessage" className="loading">Processing transfer... Please wait.</p>}

      <table>
        <thead>
          <tr>
            <th>Patient Name</th>
            <th>Origin PT</th>
            <th>Receiving PT</th>
            <th>Vaccine</th>
            <th>Transfer Status</th>
          </tr>
        </thead>
        <tbody>
          {transfers.map((transfer, index) => (
            <tr key={index}>
              <td>{transfer.patientName}</td>
              <td>{transfer.originPT}</td>
              <td>{transfer.receivingPT}</td>
              <td>{transfer.vaccine}</td>
              <td className={`status ${transfer.status === 'Transferred' ? 'transferred' : 'failed'}`}>
                {transfer.status}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Form;
