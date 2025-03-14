import { readFileSync } from 'node:fs';

import { cleanEnv, port, host, bool, makeValidator } from 'envalid';

import validator from 'validator';

const is_prod = () =>
  process.env.DEV_IS_LOCAL_ENV !== 'true' &&
  process.env.DEV_IS_TEST_ENV !== 'true';

const urlList = makeValidator((val: string) => {
  const urls = val.split(',');

  if (urls.every((url) => validator.isURL(url, { require_tld: false }))) {
    return urls;
  } else {
    throw new Error(`Expected comma seperated URL list`);
  }
});

const boolFalseIfProd = (spec: { default: boolean }) =>
  bool({
    ...spec,
    choices: is_prod() ? [false] : [false, true],
  });

const validPrivateKeyPathIfProd = makeValidator((val?: string) => {
  const path_is_valid_file = (() => {
    if (val === undefined) {
      return false;
    } else {
      const is_absolute_path = val.startsWith('/');
      const contains_path_traversal = /\/..\//.test(val);
      const has_expected_extension = /.pem$/.test(val);

      if (
        !is_absolute_path ||
        contains_path_traversal ||
        !has_expected_extension
      ) {
        throw new Error(
          'Expected an absolute path, without path traversal, with a .pem file extension',
        );
      }

      // eslint-disable-next-line security/detect-non-literal-fs-filename
      const pem_data = readFileSync(val, 'utf8');

      const is_pem_private_key =
        // eslint-disable-next-line security/detect-unsafe-regex
        /^-----BEGIN PRIVATE KEY-----(\n|\r|\r\n)([0-9a-zA-Z+/=]{64}(\n|\r|\r\n))*([0-9a-zA-Z+/=]{1,63}(\n|\r|\r\n))?-----END PRIVATE KEY-----(\n|\r|\r\n)$/.test(
          pem_data,
        );
      if (!is_pem_private_key) {
        throw new Error(
          'Key file contents do not match expected RS256 pem private key pattern.',
        );
      }

      return true;
    }
  })();

  if (is_prod() && !path_is_valid_file) {
    throw new Error(`Expected a valid path to a private key file.`);
  }

  return val;
});

export const get_env = () => {
  // NOTE: this does not populate process.env, aside from defaults. Assumes env is already populated as desired (e.g. via dotenv in the entrypoint file)
  const processed_env = cleanEnv(process.env, {
    EXPRESS_PORT: port({ default: 3000 }),
    EXPRESS_HOST: host({ default: '0.0.0.0' }),

    AGGREGATOR_URLS: urlList(),

    PRIVATE_KEY_PATH: validPrivateKeyPathIfProd<string | undefined>({
      default: is_prod() ? '/secrets/private_key.pem' : undefined,
    }),

    DEV_IS_LOCAL_ENV: boolFalseIfProd({ default: false }),
    DEV_IS_TEST_ENV: boolFalseIfProd({ default: false }),
  });

  return processed_env;
};
