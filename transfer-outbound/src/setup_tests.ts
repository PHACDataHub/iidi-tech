import dotenv from 'dotenv';

dotenv.config({ path: '.env.node-dev-docker-env-overrides' }); // relative to the call point, e.g. the service root

process.env.DEV_IS_TEST_ENV = 'true';
process.env.REDIS_PASSWORD = 'test-placeholder';
process.env.FHIR_URL = 'https://placeholder/fhir';
process.env.OWN_TRANSFER_CODE = 'BC';
process.env.INBOUND_TRANSFER_SERIVCES_BY_TRANSFER_CODE =
  '{ "ON": "http://placeholder" }';
