import dotenv from 'dotenv';

dotenv.config({ path: '.env.node-dev-docker-env-overrides' }); // relative to the call point, e.g. the service root
process.env.DEV_IS_TEST_ENV = 'true';
