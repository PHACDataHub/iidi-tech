import { get_env } from './env.ts';
import { AppError } from './error_utils.ts';

export const assert_bundle_follows_fhir_spec = async (_bundle: unknown) => {
  const { FHIR_URL } = get_env();
  try {
    // TODO implement bundle fhir spec validation here
    // https://build.fhir.org/resource-operation-validate.html
    // https://build.fhir.org/bundle.html
    // https://hl7.org/fhir/http.html#transaction

    // Throw a descriptive AppError if validation fails

    await fetch(`${FHIR_URL}/TODO");`);
  } catch (err) {
    if (err instanceof Error && !('status' in err)) {
      throw new AppError(500, err.message);
    } else {
      throw err;
    }
  }
};

export const write_bundle_to_fhir_api = async (_bundle: unknown) => {
  const { FHIR_URL } = get_env();
  try {
    // TODO implement bundle writing here
    // https://build.fhir.org/bundle.html
    // https://hl7.org/fhir/http.html#transaction

    await fetch(`${FHIR_URL}/TODO");`);
  } catch (err) {
    if (err instanceof Error && !('status' in err)) {
      throw new AppError(500, err.message);
    } else {
      throw err;
    }
  }
};
