import type { Bundle, OperationOutcome } from 'fhir/r4.d.ts';

import { get_env } from './env.ts';
import { AppError } from './error_utils.ts';

export const assert_bundle_follows_fhir_spec = async (_bundle: Bundle) => {
  const { FHIR_URL } = get_env();

  try {
    const response = await fetch(`${FHIR_URL}/Bundle/$validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(_bundle),
    });

    const operationOutcome: OperationOutcome =
      (await response.json()) as OperationOutcome;

    if (
      operationOutcome.issue &&
      operationOutcome.issue.some((issue) => issue.severity === 'error')
    ) {
      const validationErrors = operationOutcome.issue
        .filter((issue) => issue.severity === 'error')
        .map((issue) => ({
          location: issue.location?.join(', ') || 'Unknown location',
          diagnostics: issue.diagnostics || 'No additional details',
          details: issue.details?.text || 'No details provided',
        }));

      throw new AppError(400, 'FHIR spec validation failed', validationErrors);
    }
  } catch (error) {
    if (error instanceof AppError) {
      throw error;
    }
    const err = error as Error;
    throw new AppError(
      500,
      `Error during FHIR spec validation: ${err.message}`,
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
