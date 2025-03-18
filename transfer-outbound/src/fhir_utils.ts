import type { Patient, Bundle, CapabilityStatement } from 'fhir/r4.d.ts';

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

export const get_error_from_fhir_response = async (response: Response) => {
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

export const assert_patient_exists_and_can_be_transferred = async (
  patient_id: string,
) => {
  const patient = await get_patient(patient_id);

  // IMPORTANT: the logic for "can_be_transferred" must return false for a patient that has been transferred
  // (in addition to any other reasons why a patient might be un-transferable).
  // See `add_replaced_by_link_to_transferred_patient`, which is assumed to be called following a patient transfer.
  // There is a coupling between that method and this assertion check, via the underlying buisness logic

  const replaced_by = patient.link?.find(({ type }) => type === 'replaced-by');
  if (replaced_by !== undefined) {
    // See https://www.hl7.org/fhir/references.html#reference
    throw new AppError(
      400,
      `Patient "${patient_id}" exists, but is non-authoratative, having been replaced by a newer patient record. See \`Patient.link\`.`,
      replaced_by,
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

export const add_replaced_by_link_to_transferred_patient = async (
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

  const patient = await get_patient(patient_id);

  // IMPORTANT: the behaviour here is coupled to the logic of assert_patient_exists_and_can_be_transferred
  // namely, a patient "can_be_transferred" iff it has NOT been "replaced-by" another patient instance

  // References:
  //    https://www.hl7.org/fhir/patient-definitions.html#Patient.link
  //    https://www.hl7.org/fhir/valueset-link-type.html
  //    https://www.hl7.org/fhir/references.html#logical
  //    https://build.fhir.org/patient.html#links

  const replaced_by_link = {
    type: 'replaced-by',
    other: {
      type: 'Patient',
      // NOTE: something of a missuse of "display". Valid in that it describes the what (along with the why) of the referenced entity,
      // but the spec technically calls for a plain text description, so using stringified JSON maaaay be an abuse, haha. Good enough for PoC,
      // would require further refinement in future stages
      display: JSON.stringify({
        explanation: `This patient and their immunization records have been transferred from "${OWN_TRANSFER_CODE}" to "${transfer_code}".`,
        transfer_request_id, // TODO may not be unique across time; if a job is done and flushed from the queue, its ID can be reused. Maybe useful if paired with time
        transferred_from: OWN_TRANSFER_CODE,
        transferred_to: transfer_code,
        patient_id_in_recipient_system: new_patient_id ?? 'unknown',
        // TODO request timestamp? Other metadata? We don't currently require a "requestor id" or a "transfer reason" etc, and those are out of scope,
        // but those values may be useful here
      }),
      // TODO consider using `identifier` field as well, for logical reference. Main question here is whether it's worth/acceptable to
      // give one province the system URL information of another province's FHIR server
      // identifier: {
      //   system: 'TODO',
      //   value: new_patient_id,
      // },
    },
  };

  const response = await fetch(`${FHIR_URL}/Patient/${patient_id}`, {
    method: 'PATCH',
    headers: {
      'content-type': 'application/json-patch+json',
    },
    body: JSON.stringify([
      {
        op: 'add',
        // Reference: https://www.hl7.org/fhir/patient-definitions.html#Patient.active
        // "If a record is inactive, and linked to an active record, then future patient/record updates should occur on the other patient."
        // Might be debatable in this case, the "linked" record is probably active, but isn't assumed to be reachable from this system.
        // That could potantially cause problems if not handled by related provincial systems?
        path: '/active',
        value: false,
      },
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

export const is_fhir_status_active = async (): Promise<boolean> => {
  const { FHIR_URL } = get_env();

  try {
    const response = await fetch(`${FHIR_URL}/metadata`);

    if (!response.ok) {
      console.error(`FHIR metadata request failed: ${response.status}`);
      return false;
    }

    const json = (await response.json()) as CapabilityStatement;

    return json.status === 'active';
  } catch (error) {
    console.error(
      'FHIR health check failed:',
      error instanceof Error ? error.message : error,
    );
    return false;
  }
};
