import type { Patient } from 'fhir/r4.d.ts';

import { get_env } from './env.ts';
import { AppError } from './error_utils.ts';

const is_patient_resource = (json: unknown): json is Patient =>
  typeof json === 'object' &&
  json !== null &&
  'resourceType' in json &&
  json?.resourceType === 'Patient';

export const assert_patient_exists_and_is_untransfered = async (
  patient_id: string,
) => {
  const { FHIR_URL } = get_env();

  const response = await fetch(`${FHIR_URL}/Patient/${patient_id}`);
  const json = await response.json();

  if (response.status === 200) {
    if (is_patient_resource(json)) {
      // TODO transfer mark storage specific TBD, see mark_patient_transfered method
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
    const fhir_diagnostic_messages = (
      json as { issue?: [{ diagnostics?: string }] }
    )?.issue
      ?.map(({ diagnostics }) => diagnostics)
      .join(', ');

    throw new AppError(response.status, fhir_diagnostic_messages ?? '');
  }
};

export const get_patient_bundle_for_transfer = async (_patient_id: string) => {
  const { FHIR_URL } = get_env();

  // TODO
  throw new AppError(
    501,
    'Patient bundle collection method not implemented yet',
  );

  await fetch(`${FHIR_URL}/TODO`);
};

export const mark_patient_transfered = async (
  _patient_id: string,
  _transfer_request_id: string,
) => {
  const { FHIR_URL } = get_env();

  // TODO mark patient as transfered out in province FHIR server,
  // possibly with a FHIR spec extension field for the inbound province and transfer request ID,
  // expect this to happen after bundle collection step and before the bundle
  // is sent to the inbound service

  // related note: maybe we'll want a post transfer step to also add an extension/metadata field for the patient ID of the record
  // created in the inbound province?

  throw new AppError(
    501,
    'Patient transfer marking method not implemented yet',
  );

  await fetch(`${FHIR_URL}/TODO`);
};

export const unmark_patient_transfered = async (
  _patient_id: string,
  _transfer_request_id: string,
) => {
  const { FHIR_URL } = get_env();

  // TODO need to be able to revert the transfer mark if the bundle is rejected by the inbound service

  throw new AppError(
    501,
    'Patient transfer unmarking method not implemented yet',
  );

  await fetch(`${FHIR_URL}/TODO`);
};
