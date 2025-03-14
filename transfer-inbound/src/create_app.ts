import express from 'express';

import { expressErrorHandler } from './error_utils.ts';
import {
  assert_bundle_follows_fhir_spec,
  is_fhir_status_active,
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

  app.get('/healthcheck', async (_req, res) => {
    if (await is_fhir_status_active()) {
      res.status(200).send();
    } else {
      res.status(503).send();
    }
  });

  app.post('/inbound-transfer', async (req, res) => {
    const { bundle } = req.body;

    assert_is_bundle(bundle);
    assert_bundle_follows_business_rules(bundle);

    const transactionBundle = await set_bundle_type_to_transaction(bundle);

    await assert_bundle_follows_fhir_spec(transactionBundle);

    const new_patient_id = await write_bundle_to_fhir_api(transactionBundle);

    res.status(201).send({
      message: 'Patient bundle accepted by FHIR server',
      patient: { id: new_patient_id },
    });
  });

  app.get('/inbound-transfer/dry-run', async (req, res) => {
    const { bundle } = req.body;
    assert_is_bundle(bundle);
    const transactionBundle = await set_bundle_type_to_transaction(bundle);

    assert_bundle_follows_business_rules(transactionBundle);

    await assert_bundle_follows_fhir_spec(transactionBundle);

    res.status(200).send({
      message:
        'Dry run successful, provided patient bundle would have been accepted by FHIR server',
    });
  });

  app.use(expressErrorHandler);

  return app;
};
