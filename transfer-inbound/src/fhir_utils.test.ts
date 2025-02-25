import type { Bundle } from 'fhir/r4.d.ts';

import { get_env } from './env.ts';
import { AppError } from './error_utils.ts';
import { assert_bundle_follows_fhir_spec } from './fhir_utils.ts';
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
});
