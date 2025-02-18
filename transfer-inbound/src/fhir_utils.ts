import { get_env } from './env.ts';
import { AppError } from './error_utils.ts';

export const assert_bundle_follows_fhir_spec = async (_bundle: unknown) => {
  const { FHIR_URL } = get_env();
  // TODO implement bundle fhir spec validation here
  // Throw a descriptive AppError if validation fails

  // References:
  // https://build.fhir.org/resource-operation-validate.html
  // https://build.fhir.org/bundle.html
  // https://hl7.org/fhir/http.html#transaction

  throw new AppError(501, 'FHIR spec validation not implemented');

  await fetch(`${FHIR_URL}/TODO`);
};

export const write_bundle_to_fhir_api = async (_bundle: unknown) => {
  const { FHIR_URL } = get_env();
  // TODO implement bundle writing here

  // References:
  // https://build.fhir.org/bundle.html
  // https://hl7.org/fhir/http.html#transaction

  throw new AppError(501, 'Writing to FHIR API not implemented');

  await fetch(`${FHIR_URL}/TODO`);
};
