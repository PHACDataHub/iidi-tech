import { cleanEnv, port, host, bool, url, str, makeValidator } from 'envalid';

import validator from 'validator';

import { transfer_codes, is_transfer_code } from './transfer_code_utils.ts';
import type { transferCode as transferCodeType } from './transfer_code_utils.ts';

const transferCode = makeValidator((val: string) => {
  if (is_transfer_code(val)) {
    return val;
  } else {
    throw new Error(`Expected PT code (${transfer_codes.join(', ')})`);
  }
});

const urlByTransferCode = makeValidator((val: string) => {
  const pt_url_map = JSON.parse(val);

  if (
    Object.keys(pt_url_map).every(is_transfer_code) &&
    Object.values(pt_url_map).every(
      (value) =>
        typeof value === 'string' &&
        validator.isURL(value, { require_tld: false }),
    )
  ) {
    return pt_url_map as Record<transferCodeType, string>;
  } else {
    throw new Error(
      `Expected JSON string mapping PT codes (${transfer_codes.join(', ')}) to transfer-inbound service URLs`,
    );
  }
});

const originList = makeValidator((val: string) => {
  if (val === '*') {
    return val;
  } else {
    const url_list = val.split(',');
    if (
      url_list.every((value) => validator.isURL(value, { require_tld: false }))
    ) {
      return url_list;
    } else {
      throw new Error(
        `Expected JSON string mapping PT codes (${transfer_codes.join(', ')}) to transfer-inbound service URLs`,
      );
    }
  }
});

const boolFalseIfProd = (spec: { default: boolean }) => {
  const is_prod =
    process.env.DEV_IS_LOCAL_ENV !== 'true' &&
    process.env.DEV_IS_TEST_ENV !== 'true';

  return bool({
    ...spec,
    choices: is_prod ? [false] : [false, true],
  });
};

export const get_env = () => {
  // NOTE: this does not populate process.env, aside from defaults. Assumes env is already populated as desired (e.g. via dotenv in the entrypoint file)
  const processed_env = cleanEnv(process.env, {
    EXPRESS_PORT: port({ default: 3000 }),
    EXPRESS_HOST: host({ default: '0.0.0.0' }),

    REDIS_PORT: port({ default: 6379 }),
    REDIS_PASSWORD: str(),
    REDIS_HOST: host({ default: '0.0.0.0' }),

    FHIR_URL: url(),

    OWN_TRANSFER_CODE: transferCode(),
    INBOUND_TRANSFER_SERIVCES_BY_TRANSFER_CODE: urlByTransferCode(),

    // Only for configuring CORS for PoC demo purposes, in reality this is expected to be an
    // internal server-to-server API, with no direct frontend access
    TRANSFER_DASHBOARD_ORIGINS: originList({ default: '*' }),

    DEV_IS_LOCAL_ENV: boolFalseIfProd({ default: false }),
    DEV_IS_TEST_ENV: boolFalseIfProd({ default: false }),
  });

  return processed_env;
};
