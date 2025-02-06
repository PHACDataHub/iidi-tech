import dotenv from 'dotenv';
import { enableFetchMocks } from 'jest-fetch-mock';

enableFetchMocks();

dotenv.config({ path: '.env.node-dev-docker-env-overrides' }); // relative to the call point, e.g. the service root
process.env.DEV_IS_TEST_ENV = 'true';

// placeholder so env.ts' validation passes by default. Individual tests that depend on a specific AGGREGATOR_URLS
// value should override/revert as a pre and post test step
process.env.AGGREGATOR_URLS = 'http://localhost:8080/placeholder/';
