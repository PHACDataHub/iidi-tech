import { cleanEnv, port, host, bool } from 'envalid';

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

    DEV_IS_LOCAL_ENV: boolFalseIfProd({ default: false }),
    DEV_IS_TEST_ENV: boolFalseIfProd({ default: false }),
  });

  return processed_env;
};
