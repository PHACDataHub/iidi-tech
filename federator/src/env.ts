import { cleanEnv, port, host, bool, makeValidator } from 'envalid';

import validator from 'validator';

const urlList = makeValidator((val: string) => {
  const urls = val.split(',');

  if (urls.every((url) => validator.isURL(url, { require_tld: false }))) {
    return urls;
  } else {
    throw new Error(`Expected comma seperated URL list`);
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

    AGGREGATOR_URLS: urlList(),

    DEV_IS_LOCAL_ENV: boolFalseIfProd({ default: false }),
    DEV_IS_TEST_ENV: boolFalseIfProd({ default: false }),
  });

  return processed_env;
};
