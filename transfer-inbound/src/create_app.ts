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

    // The HAPI FHIR server attaches a meta object to each resource which contains information
    // about the resource, such as its version, last updated time, and source.
    // The source field is prepopulated by the HAPI FHIR server with the URL of the server itself.
    // However, in our case the server sets a random value which does not correspond to the URL format (Reason: TODO).
    // Docker image v8.2.0-1 onwards $validate calls to the HAPI FHIR server throws an error if the source 
    // field is not in the correct format. Safest approach is to remove the source field from the resources.
    transactionBundle.entry?.map(entry => {
      delete entry.resource?.meta?.source; // remove meta.source information from resources
    });

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
