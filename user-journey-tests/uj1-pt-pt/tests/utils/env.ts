import { cleanEnv, url, num } from 'envalid';

export const get_env = () => {
  return cleanEnv(process.env, {
    BC_OUTBOUND_URL: url({ default: 'http://localhost:8080/bc/outbound' }),
    ON_OUTBOUND_URL: url({ default: 'http://localhost:8080/on/outbound' }),
    BC_FHIR_URL: url({ default: 'http://localhost:8080/bc/fhir' }),
    ON_FHIR_URL: url({ default: 'http://localhost:8080/on/fhir' }),
    MAX_RETRIES: num({ default: 5 }),
    RETRY_DELAY: num({ default: 2000 }),
  });
};
