import type {
  Bundle,
  CapabilityStatement,
  OperationOutcome,
} from 'fhir/r4.d.ts';

import { get_env } from './env.ts';
import { AppError } from './error_utils.ts';

export const set_bundle_type_to_transaction = async (bundle: Bundle) => ({
  resourceType: bundle.resourceType,
  type: 'transaction' as const,
  entry: bundle?.entry?.map(({ resource, fullUrl }) => ({
    resource,
    request: {
      method: 'POST' as const,
      url: resource?.resourceType || 'UNKNOWN RESOURCE TYPE',
    },
    fullUrl,
  })),
});

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
      throw new AppError(
        500,
        'FHIR spec validation encountered a server error',
        serverErrors,
      );
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

export const handle_response = async (response: Response) => {
  // FHIR server treats as transaction and rolls back for errors.
  if (!response.ok) {
    throw new AppError(
      response.status,
      `FHIR server responded with status ${response.status}`,
    );
  }

  const transactionResponse = await response.json().catch(() => null);

  if (
    typeof transactionResponse === 'object' &&
    transactionResponse &&
    'resourceType' in transactionResponse &&
    'type' in transactionResponse &&
    'entry' in transactionResponse &&
    Array.isArray(transactionResponse.entry) &&
    transactionResponse.entry.length > 0
  ) {
    return transactionResponse as Bundle;
  }

  throw new AppError(
    500,
    `FHIR server responded with status ${response.status} but unexpected response body.`,
  );
};

export const write_bundle_to_fhir_api = async (
  bundle: Bundle,
): Promise<string> => {
  const { FHIR_URL } = get_env();

  const response = await fetch(FHIR_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/fhir+json',
    },
    // Force FHIR server to treat operations as a transaction for integrity.
    // This assumes that data integrity managed by the FHIR server.
    body: JSON.stringify(bundle),
  });

  const bundleResponse = await handle_response(response);

  // Get Patient id from response
  const patientEntry = bundleResponse?.entry?.find((entry) =>
    entry.response?.location?.startsWith('Patient/'),
  );
  if (!patientEntry) {
    throw new AppError(
      500,
      'Patient resource not found in transaction response',
    );
  }

  const patientId = patientEntry.response?.location?.split('/')[1] || null;
  if (!patientId) {
    throw new AppError(
      500,
      'Unexpected error: Patient ID not found in response',
    );
  }

  return patientId;
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
