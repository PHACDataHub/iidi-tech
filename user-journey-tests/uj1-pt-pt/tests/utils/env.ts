import { cleanEnv, url, num } from 'envalid';

export const get_env = () => {
  return cleanEnv(process.env, {
    BC_OUTBOUND_URL: url({ default: 'http://localhost:3000' }),
    ON_OUTBOUND_URL: url({ default: 'http://localhost:3001' }),
    BC_FHIR_URL: url({ default: 'http://localhost:3002' }),
    ON_FHIR_URL: url({ default: 'http://localhost:3003' }),
    MAX_RETRIES: num({ default: 5 }),
    RETRY_DELAY: num({ default: 2000 }),
  });
};
