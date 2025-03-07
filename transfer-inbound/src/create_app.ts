import express from 'express';

import { expressErrorHandler } from './error_utils.ts';
import {
  assert_bundle_follows_fhir_spec,
  set_bundle_type_to_transaction,
  write_bundle_to_fhir_api,
} from './fhir_utils.ts';
import {
  assert_bundle_follows_business_rules,
  assert_is_bundle,
} from './validation_utils.ts';

export const create_app = async () => {
  const app = express();

  // we'll need to be able to read `X-Forwarded-*` headers, both in prod and when using the dev docker setup
  app.set('trust proxy', true);

  app.use(express.json()); // parses JSON body payloads, converts req.body from a string to object
  app.use(express.urlencoded({ extended: false })); // parses URL-encoded payload parameters on POST/PUT in to req.body fields

  app.get('/healthcheck', (_req, res) => {
    // TODO consider if a non-trivial healthcheck is appropriate/useful
    res.status(200).send();
  });

  app.post('/inbound-transfer', async (req, res) => {
    const { bundle } = req.body;

    assert_is_bundle(bundle);
    assert_bundle_follows_business_rules(bundle);

    const transactionBundle = await set_bundle_type_to_transaction(bundle);

    // TODO might be redundant to write_bundle_to_fhir_api, depends if FHIR servers are configured to validate pre-write
    await assert_bundle_follows_fhir_spec(transactionBundle);

    const new_patient_id = await write_bundle_to_fhir_api(transactionBundle);

    res.status(200).send({ new_patient_id });
  });

  app.get('/inbound-transfer/dry-run', async (req, res) => {
    const { bundle } = req.body;
    assert_is_bundle(bundle);
    const transactionBundle = await set_bundle_type_to_transaction(bundle);

    assert_bundle_follows_business_rules(transactionBundle);

    await assert_bundle_follows_fhir_spec(transactionBundle);

    res.status(200).send();
  });

  app.use(expressErrorHandler);

  return app;
};
