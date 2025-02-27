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

const handle_fhir_response_error = async (response: Response) => {
  const json = (await response.json().catch(() => null)) as {
    issue?: [{ diagnostics?: string }];
  } | null;

  const fhir_diagnostic_messages = json?.issue
    ?.map(({ diagnostics }) => diagnostics)
    .join(', ');

  if (fhir_diagnostic_messages !== undefined) {
    throw new AppError(response.status, fhir_diagnostic_messages);
  } else {
    throw new AppError(
      response.status,
      `FHIR request returned code "${response.status}", no diagnostic messages available`,
    );
  }
};

export const assert_patient_exists_and_is_untransfered = async (
  patient_id: string,
) => {
  assert_patient_id_parameter_is_valid(patient_id);

  const { FHIR_URL } = get_env();

  const response = await fetch(`${FHIR_URL}/Patient/${patient_id}`);

  if (response.ok) {
    const json = await response.json().catch(() => null);

    if (is_patient_resource(json)) {
      // TODO transfer mark storage specific TBD, see set_patient_transfer_metadata_and_lock method
      const patient_transfered_to = json.extension?.find(
        ({ url }) =>
          url ===
          'TODO if we want to store transfer status as an extension, we need to publish the spec def at a known url',
      )?.valueString;

      if (patient_transfered_to !== undefined) {
        throw new AppError(
          400,
          `Patient "${patient_id}" exists, but has already been transfered out to "${patient_transfered_to}"`,
        );
      }
    } else {
      throw new AppError(
        500,
        `FHIR server returned a non-Patient resource for id "${patient_id}". This should never happen`,
      );
    }
  } else {
    await handle_fhir_response_error(response);
  }
};

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
    await handle_fhir_response_error(response);
  }
};

export const set_patient_transfer_metadata_and_lock = async (
  patient_id: string,
  _transfer_request_id: string,
  transfer_to: transferCode,
  // TODO other transfer metadata might be relevant to store, but likely not in scope right now
) => {
  assert_patient_id_parameter_is_valid(patient_id);
  assert_transfer_code_parameter_is_valid(transfer_to);

  // TODO mark patient as being transfered out in outbound province FHIR server,
  // possibly with a FHIR spec extension field for the inbound province and transfer request ID,
  // expect this to happen after bundle collection step and before the bundle
  // is sent to the inbound service

  // const { FHIR_URL } = get_env();

  // await fetch(`${FHIR_URL}/TODO`);
};

export const unset_patient_transfer_metadata_and_lock = async (
  patient_id: string,
  _transfer_request_id: string,
) => {
  assert_patient_id_parameter_is_valid(patient_id);

  // TODO need to be able to revert the transfer mark if the bundle is rejected by the inbound service

  // const { FHIR_URL } = get_env();

  // await fetch(`${FHIR_URL}/TODO`);
};

export const set_patient_post_transfer_metadata = async (
  patient_id: string,
  _transfer_request_id: string,
  new_patient_id?: string,
) => {
  assert_patient_id_parameter_is_valid(patient_id);
  if (new_patient_id !== undefined) {
    assert_patient_id_parameter_is_valid(new_patient_id);
  }

  // TODO mark patient as fully transfered out in province FHIR server, add id of patient in inbound system
  // Might not want to assume the inbound province shared a new patient ID, cover case where it's undefined

  // const { FHIR_URL } = get_env();

  // await fetch(`${FHIR_URL}/TODO`);
};
