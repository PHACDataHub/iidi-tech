import type { Patient, Bundle } from 'fhir/r4.d.ts';

import { get_env } from './env.ts';
import { AppError } from './error_utils.ts';
import {
  assert_patient_id_parameter_is_valid,
  assert_transfer_code_parameter_is_valid,
} from './request_parameter_validation_utils.ts';
import type { transferCode } from './transfer_code_utils.ts';

const is_patient_resource = (json: unknown): json is Patient =>
  typeof json === 'object' &&
  json !== null &&
  'resourceType' in json &&
  json?.resourceType === 'Patient';

const is_bundle_resource = (json: unknown): json is Bundle =>
  typeof json === 'object' &&
  json !== null &&
  'resourceType' in json &&
  json?.resourceType === 'Bundle';

const get_error_from_fhir_response = async (response: Response) => {
  const json = (await response.json().catch(() => null)) as {
    issue?: [{ diagnostics?: string }];
  } | null;

  const fhir_diagnostic_messages = json?.issue
    ?.map(({ diagnostics }) => diagnostics)
    .join(', ');

  if (fhir_diagnostic_messages !== undefined) {
    return new AppError(response.status, fhir_diagnostic_messages);
  } else {
    return new AppError(
      response.status,
      `FHIR request returned code "${response.status}", no diagnostic messages available`,
    );
  }
};

const get_patient = async (patient_id: string) => {
  assert_patient_id_parameter_is_valid(patient_id);

  const { FHIR_URL } = get_env();

  const response = await fetch(`${FHIR_URL}/Patient/${patient_id}`);

  if (response.ok) {
    const json = await response.json().catch(() => null);

    if (is_patient_resource(json)) {
      return json;
    } else {
      throw new AppError(
        500,
        `Invalid response from FHIR server for patient ID "${patient_id}": response status was "ok", but response body was not a valid Patient resource`,
      );
    }
  } else {
    throw await get_error_from_fhir_response(response);
  }
};

export const assert_patient_exists_and_can_be_transfered = async (
  patient_id: string,
) => {
  const patient = await get_patient(patient_id);

  const replaced_by = patient.link?.find(({ type }) => type === 'replaced-by');
  if (replaced_by !== undefined) {
    // See https://www.hl7.org/fhir/references.html#reference
    throw new AppError(
      400,
      `Patient "${patient_id}" exists, but is non-authoratative, having been replaced by a newer patient record. See reference:\n` +
        JSON.stringify(replaced_by, null, 2),
    );
  }
};

// TODO: might be worth having a short-lived in-memory cache here, to spare the FHIR thrashing if retries occur during the work loop
export const get_patient_bundle_for_transfer = async (patient_id: string) => {
  assert_patient_id_parameter_is_valid(patient_id);

  const { FHIR_URL } = get_env();

  const response = await fetch(
    // TODO get _type list, possible other search rules, from configuration (issue #110)?
    // eslint-disable-next-line no-secrets/no-secrets
    `${FHIR_URL}/Patient/${patient_id}/$everything?_type=Patient,Immunization,AllergyIntolerance`,
  );

  if (response.ok) {
    const json = await response.json().catch(() => null);

    if (is_bundle_resource(json)) {
      return json;
    } else {
      throw new AppError(
        500,
        `Invalid response from FHIR server for patient ID "${patient_id}": response status was "ok", but response body was not a valid Bundle resource`,
      );
    }
  } else {
    throw await get_error_from_fhir_response(response);
  }
};

export const set_replaced_by_link_on_transfered_patient = async (
  patient_id: string,
  transfer_request_id: string,
  transfer_code: transferCode,
  new_patient_id?: string,
) => {
  assert_patient_id_parameter_is_valid(patient_id);
  assert_transfer_code_parameter_is_valid(transfer_code);
  if (new_patient_id !== undefined) {
    assert_patient_id_parameter_is_valid(new_patient_id);
  }

  const { FHIR_URL, OWN_TRANSFER_CODE } = get_env();

  // IMPORTANT: the behaviour here is tightly coupled to the logic of assert_patient_exists_and_can_be_transfered

  // References:
  //    https://www.hl7.org/fhir/patient-definitions.html#Patient.link
  //    https://www.hl7.org/fhir/valueset-link-type.html
  //    https://www.hl7.org/fhir/references.html#logical
  //    https://build.fhir.org/patient.html#links

  const patient = await get_patient(patient_id);

  const replaced_by_link = {
    type: 'replaced-by',
    other: {
      type: 'Patient',
      display: JSON.stringify({
        explanation: `This patient and their immunization records have been transfered from "${OWN_TRANSFER_CODE}" to "${transfer_code}".`,
        transfer_request_id,
        transfered_from: OWN_TRANSFER_CODE,
        transfered_to: transfer_code,
        patient_id_in_recipient_system: new_patient_id ?? 'unknown',
      }),
      identifier: {
        system: 'TODO', // TODO considering having the inbound system return the URL of the receiving FHIR server, even if it can't be reached externally
        value: new_patient_id,
      },
    },
  };

  const response = await fetch(`${FHIR_URL}/Patient/${patient_id}`, {
    method: 'PATCH',
    headers: {
      'content-type': 'application/json-patch+json',
    },
    body: JSON.stringify([
      patient?.link !== undefined
        ? {
            op: 'add',
            path: '/link/-', // push to existing link array
            value: replaced_by_link,
          }
        : {
            op: 'add',
            path: '/link', // make new link array
            value: [replaced_by_link],
          },
    ]),
  });

  if (!response.ok) {
    throw await get_error_from_fhir_response(response);
  }
};
