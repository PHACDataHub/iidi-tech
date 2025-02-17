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

  try {
    const response = await fetch(`${FHIR_URL}/Patient/${patient_id}`);
    const json = await response.json();

    if (response.status === 200) {
      if (is_patient_resource(json)) {
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
  } catch (err) {
    if (err instanceof Error && !('status' in err)) {
      throw new AppError(500, err.message);
    } else {
      throw err;
    }
  }
};
