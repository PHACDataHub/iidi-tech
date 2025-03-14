import './TransferForm.css';

import {
  GcdsInput,
  GcdsSelect,
  GcdsButton,
  GcdsNotice,
  GcdsText,
  GcdsHeading,
} from '@cdssnc/gcds-components-react';
import { useState, useEffect } from 'react';

import {
  pt_codes,
  transfer_service_url_by_pt_code,
  pt_name_by_code,
} from 'src/pt_utils.js';

const TransferForm = ({ outboundPT }) => {
  const transfer_service_url = transfer_service_url_by_pt_code[outboundPT];
  const default_inbound_pt = pt_codes.find((pt) => pt !== outboundPT);

  const [patientId, setPatientId] = useState('');
  const [patientIdErrorMessage, setPatientIdErrorMessage] = useState('');

  const [inboundPT, setInboundPT] = useState(default_inbound_pt);

  const [loading, setLoading] = useState(false);
  const [showLoading, setShowLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [transferRequest, setTransferRequest] = useState();

  const should_disable_submit_buttom =
    !patientId || patientIdErrorMessage || showLoading;

  const handlePatientIdInput = (e) => {
    e.stopPropagation();

    const new_patient_id = e.target.value;

    if (!/^[1-9][0-9]*$/.test(new_patient_id)) {
      setPatientIdErrorMessage(
        'Patient ID should be a positive integer value.',
      );
    } else {
      setPatientIdErrorMessage('');
    }
    setPatientId(new_patient_id);
  };

  const submitTransferRequest = async () => {
    if (should_disable_submit_buttom) {
      return;
    }

    setErrorMessage('');
    setTransferRequest(undefined);
    setLoading(true);

    try {
      const response = await fetch(`${transfer_service_url}/transfer-request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          transfer_to: inboundPT,
        }),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          `Failed to initiate transfer: ${'error' in data ? data.error : response.statusText}`,
        );
      } else {
        if (data) {
          setTransferRequest(data);
        } else {
          throw new Error(
            'Transfer service did not respond with expected data, please contact a developer.',
          );
        }
      }
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <>
      <GcdsHeading tag="h2">Initiate New Transfer</GcdsHeading>
      <form
        className="transfer-request-form"
        onSubmit={(e) => e.preventDefault()}
      >
        <div className="transfer-request-form__field-row">
          <GcdsInput
            inputId="patientId"
            label="Patient ID"
            name="patientId"
            hint={`ID of a patient in ${pt_name_by_code[outboundPT]}'s system`}
            errorMessage={patientIdErrorMessage}
            value={patientId}
            onChange={handlePatientIdInput}
            onKeyUp={handlePatientIdInput}
          />

          <GcdsSelect
            selectId="inboundPT"
            label="Receiving PT"
            name="inboundPT"
            hint="Province or Teritory to transfer records to"
            value={inboundPT}
            onChange={(e) => {
              const new_receiving_pt = e.target.value;
              setInboundPT(new_receiving_pt);
            }}
          >
            {pt_codes
              .filter((code) => code !== outboundPT)
              .map((pt) => (
                <option value={pt} index={pt}>
                  {pt_name_by_code[pt]}
                </option>
              ))}
          </GcdsSelect>
        </div>

        <GcdsButton
          disabled={should_disable_submit_buttom}
          onClick={submitTransferRequest}
        >
          {!showLoading ? 'Initiate transfer' : 'Awaiting response...'}
        </GcdsButton>

        {(errorMessage || transferRequest) && (
          <div style={{ paddingTop: '20px' }}>
            <GcdsNotice
              type={errorMessage ? 'danger' : 'success'}
              noticeTitleTag="h3"
              noticeTitle={errorMessage ? 'Error' : 'Success'}
            >
              <GcdsText>
                {errorMessage ||
                  `Transfer Request created (transfer job ID ${transferRequest.job_id}), transfering the patient with ID ${transferRequest.patient_id} ` +
                    `from ${pt_name_by_code[outboundPT]} to ${pt_name_by_code[transferRequest.transfer_to]}.`}
              </GcdsText>
            </GcdsNotice>
          </div>
        )}
      </form>
    </>
  );
};

export default TransferForm;
