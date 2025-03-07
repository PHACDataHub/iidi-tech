import type { Bundle, FhirResource } from 'fhir/r4.d.ts';

import { get_env } from './env.ts';
import { AppError } from './error_utils.ts';
import {
  assert_bundle_follows_fhir_spec,
  handle_response,
  set_bundle_type_to_transaction,
  write_bundle_to_fhir_api,
} from './fhir_utils.ts';
import {
  ALLERGY_INTOLERANCE_1,
  createTransactionBundle,
  IMMUNIZATION_1,
  PATIENT_1,
} from './test_utils.ts';

// Mocking environment variable for FHIR_URL
jest.mock('./env.ts', () => ({
  get_env: jest.fn(),
}));

// Mocking the fetch function
global.fetch = jest.fn();

describe('assert_bundle_follows_fhir_spec', () => {
  let mockBundle: Bundle;

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();

    (get_env as jest.Mock).mockReturnValue({ FHIR_URL: 'https://pt-fhir.com' });

    mockBundle = createTransactionBundle(
      PATIENT_1,
      IMMUNIZATION_1,
      ALLERGY_INTOLERANCE_1,
    ) as Bundle;
  });

  it('should throw a validation error if the FHIR bundle is invalid', async () => {
    const mockResponse = {
      issue: [
        {
          severity: 'error',
          location: ['bundle.entry'],
          diagnostics: 'Invalid entry in bundle',
          details: { text: 'Entry does not follow FHIR spec' },
        },
      ],
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce(mockResponse),
    });

    // Expecting the function to throw an AppError with status 400
    await expect(assert_bundle_follows_fhir_spec(mockBundle)).rejects.toThrow(
      new AppError(400, 'FHIR spec validation failed', [
        {
          location: 'bundle.entry',
          diagnostics: 'Invalid entry in bundle',
          details: 'Entry does not follow FHIR spec',
        },
      ]),
    );
  });

  it('should not throw an error if the FHIR bundle is valid', async () => {
    const mockResponse = {
      issue: [],
    };

    // Mocking fetch to return a valid response
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValueOnce(mockResponse),
    });

    // We expect no error to be thrown when the validation is successful
    await expect(
      assert_bundle_follows_fhir_spec(mockBundle),
    ).resolves.toBeUndefined();
  });

  it('should throw a 500 error if fetch fails', async () => {
    // Mocking fetch to simulate a failure
    (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network Error'));

    // Expecting the function to throw a 500 AppError
    await expect(assert_bundle_follows_fhir_spec(mockBundle)).rejects.toThrow(
      new AppError(500, 'Error during FHIR spec validation: Network Error'),
    );
  });

  it('should throw a 500 error when response has no issues field', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValueOnce({}),
    });

    await expect(assert_bundle_follows_fhir_spec(mockBundle)).rejects.toThrow(
      new AppError(
        200,
        'Unexpected Error: FHIR validation request returned code "200", with no OperationOutcome available',
      ),
    );
  });

  it('should throw a 500 error when server returns validation errors', async () => {
    const serverErrors = {
      issue: [
        {
          severity: 'error',
          code: 'invalid',
          diagnostics: 'Server validation failed',
        },
      ],
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: jest.fn().mockResolvedValueOnce(serverErrors),
    });

    await expect(assert_bundle_follows_fhir_spec(mockBundle)).rejects.toThrow(
      new AppError(500, 'FHIR spec validation failed', serverErrors.issue),
    );
  });

  it('should handle JSON parse failure in response', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      status: 200,
      json: jest.fn().mockRejectedValueOnce(new Error('Invalid JSON')),
    });

    await expect(assert_bundle_follows_fhir_spec(mockBundle)).rejects.toThrow(
      new AppError(
        200,
        'Unexpected Error: FHIR validation request returned code "200", with no OperationOutcome available',
      ),
    );
  });

  it('should handle validation errors without location or diagnostics', async () => {
    const mockResponse = {
      issue: [
        {
          severity: 'error',
          // Deliberately omitting location and diagnostics
        },
      ],
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValueOnce(mockResponse),
    });

    await expect(assert_bundle_follows_fhir_spec(mockBundle)).rejects.toThrow(
      new AppError(400, 'FHIR spec validation failed', [
        {
          location: 'Unknown location',
          diagnostics: 'No additional details',
          details: 'No details provided',
        },
      ]),
    );
  });
});

describe('handle_response', () => {
  it('should throw AppError when response is not ok', async () => {
    const mockResponse = new Response(null, {
      status: 404,
      statusText: 'Not Found',
    });

    await expect(handle_response(mockResponse)).rejects.toThrow(
      new AppError(500, 'FHIR server responded with status 404'),
    );
  });

  it('should throw AppError when response body is invalid', async () => {
    const mockResponse = new Response(JSON.stringify({ invalid: 'response' }), {
      status: 200,
    });

    await expect(handle_response(mockResponse)).rejects.toThrow(
      new AppError(
        500,
        'FHIR server responded with status 200 but unexpected response body.',
      ),
    );
  });

  it('should return Bundle when response is valid', async () => {
    const mockBundle = {
      resourceType: 'Bundle',
      type: 'transaction-response',
      entry: [{ response: { status: '201', location: 'Patient/123' } }],
    };

    const mockResponse = new Response(JSON.stringify(mockBundle), {
      status: 200,
    });

    const result = await handle_response(mockResponse);
    expect(result).toEqual(mockBundle);
  });
});

describe('write_bundle_to_fhir_api', () => {
  let mockBundle: Bundle;

  beforeEach(() => {
    jest.clearAllMocks();
    (get_env as jest.Mock).mockReturnValue({ FHIR_URL: 'https://pt-fhir.com' });
    mockBundle = createTransactionBundle(
      PATIENT_1,
      IMMUNIZATION_1,
      ALLERGY_INTOLERANCE_1,
    );
  });

  it('should successfully write bundle and return patient ID', async () => {
    const mockBundleResponse = {
      resourceType: 'Bundle',
      type: 'transaction-response',
      entry: [
        { response: { status: '201', location: 'Patient/123' } },
        { response: { status: '201', location: 'Immunization/456' } },
      ],
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValue(mockBundleResponse),
    });

    const result = await write_bundle_to_fhir_api(mockBundle);
    expect(result).toBe('123');
  });

  it('should throw error when patient resource is not found in response', async () => {
    const mockBundleResponse = {
      resourceType: 'Bundle',
      type: 'transaction-response',
      entry: [{ response: { status: '201', location: 'Immunization/456' } }],
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValue(mockBundleResponse),
    });

    await expect(write_bundle_to_fhir_api(mockBundle)).rejects.toThrow(
      new AppError(500, 'Patient resource not found in transaction response'),
    );
  });

  it('should throw error when patient ID is missing in response', async () => {
    const mockBundleResponse = {
      resourceType: 'Bundle',
      type: 'transaction-response',
      entry: [{ response: { status: '201', location: 'Patient/' } }],
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValue(mockBundleResponse),
    });

    await expect(write_bundle_to_fhir_api(mockBundle)).rejects.toThrow(
      new AppError(500, 'Unexpected error: Patient ID not found in response'),
    );
  });
});

describe('set_bundle_type_to_transaction', () => {
  it('should correctly transform bundle to transaction type', async () => {
    const inputBundle: Bundle = {
      resourceType: 'Bundle',
      type: 'collection',
      entry: [
        {
          resource: {
            resourceType: 'Patient',
            id: '123',
          },
          fullUrl: 'urn:uuid:123',
        },
      ],
    };

    const expectedOutput = {
      resourceType: 'Bundle',
      type: 'transaction',
      entry: [
        {
          resource: {
            resourceType: 'Patient',
            id: '123',
          },
          request: {
            method: 'POST',
            url: 'Patient',
          },
          fullUrl: 'urn:uuid:123',
        },
      ],
    };

    const result = await set_bundle_type_to_transaction(inputBundle);
    expect(result).toEqual(expectedOutput);
  });

  it('should handle bundle with multiple entries', async () => {
    const inputBundle = createTransactionBundle(
      PATIENT_1,
      IMMUNIZATION_1,
      ALLERGY_INTOLERANCE_1,
    );
    const result = await set_bundle_type_to_transaction(inputBundle);

    expect(result.type).toBe('transaction');
    expect(result.entry?.length).toBe(3);
    result.entry?.forEach((entry) => {
      expect(entry.request).toBeDefined();
      expect(entry.request.method).toBe('POST');
      expect(entry.request.url).toBe(entry.resource?.resourceType);
    });
  });

  it('should handle missing resource type with fallback value', async () => {
    const inputBundle: Bundle = {
      resourceType: 'Bundle',
      type: 'collection',
      entry: [
        {
          resource: {} as FhirResource,
          fullUrl: 'urn:uuid:123',
        },
      ],
    };

    const result = await set_bundle_type_to_transaction(inputBundle);
    expect(result.entry?.[0].request.url).toBe('UNKNOWN RESOURCE TYPE');
  });
});
