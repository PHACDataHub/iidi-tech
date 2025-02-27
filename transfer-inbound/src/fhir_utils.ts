import type { Bundle, OperationOutcome } from 'fhir/r4.d.ts';

import { get_env } from './env.ts';
import { AppError } from './error_utils.ts';

export const assert_bundle_follows_fhir_spec = async (bundle: Bundle) => {
  const { FHIR_URL } = get_env();

  try {
    const response = await fetch(`${FHIR_URL}/Bundle/$validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(bundle),
    });

    const responseBody = (await response
      .json()
      .catch(() => null)) as OperationOutcome | null;

    if (!responseBody?.issue) {
      throw new AppError(
        response.status,
        `Unexpected Error: FHIR validation request returned code "${response.status}", with no OperationOutcome available`,
      );
    }
    if (response.ok) {
      const validationErrors = responseBody.issue
        .filter((issue) => issue.severity === 'error')
        .map((issue) => ({
          location: issue.location?.join(', ') || 'Unknown location',
          diagnostics: issue.diagnostics || 'No additional details',
          details: issue.details?.text || 'No details provided',
        }));

      if (validationErrors.length > 0) {
        throw new AppError(
          400,
          'FHIR spec validation failed',
          validationErrors,
        );
      }
    } else {
      const serverErrors = responseBody.issue;
      throw new AppError(500, 'FHIR spec validation failed', serverErrors);
    }
  } catch (error) {
    if (error instanceof AppError) {
      throw error;
    }
    throw new AppError(
      500,
      `Error during FHIR spec validation: ${(error as Error).message}`,
    );
  }
};

export const write_bundle_to_fhir_api = async (_bundle: Bundle) => {
  const { FHIR_URL } = get_env();
  // TODO implement bundle writing here

  // References:
  // https://build.fhir.org/bundle.html
  // https://hl7.org/fhir/http.html#transaction

  throw new AppError(501, 'Writing to FHIR API not implemented');

  await fetch(`${FHIR_URL}/TODO`);
};
