import FHIR from 'fhirclient';

import { get_env } from './env.ts';
import { AppError } from './error_utils.ts';

const get_fhir_client = () => {
  const { FHIR_URL } = get_env();
  return FHIR.client(FHIR_URL);
};

export const assert_bundle_follows_fhir_spec = async (_bundle: unknown) => {
  // TODO: the fhirclient library looked useful at a glance, but if it isn't making things easier
  // then drop and use raw fetch
  const fhir_client = get_fhir_client(); // https://docs.smarthealthit.org/client-js/client

  try {
    // TODO implement bundle fhir spec validation here
    // https://build.fhir.org/resource-operation-validate.html
    // https://build.fhir.org/bundle.html
    // https://hl7.org/fhir/http.html#transaction

    // Throw a descriptive AppError if validation fails

    await fhir_client.request('TODO');
  } catch (err) {
    if (err instanceof Error && !('status' in err)) {
      throw new AppError(500, err.message);
    } else {
      throw err;
    }
  }
};

export const write_bundle_to_fhir_api = async (_bundle: unknown) => {
  // TODO: the fhirclient library looked useful at a glance, but if it isn't making things easier
  // then drop and use raw fetch
  const fhir_client = get_fhir_client(); // https://docs.smarthealthit.org/client-js/client

  try {
    // TODO implement bundle writing here
    // https://build.fhir.org/bundle.html
    // https://hl7.org/fhir/http.html#transaction

    await fhir_client.request('TODO');
  } catch (err) {
    if (err instanceof Error && !('status' in err)) {
      throw new AppError(500, err.message);
    } else {
      throw err;
    }
  }
};
