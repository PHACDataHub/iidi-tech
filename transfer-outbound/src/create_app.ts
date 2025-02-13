import express from 'express';

import { expressErrorHandler } from './error_utils.ts';
import { initialize_transfer_request } from './transfer_request_utils.ts';

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

  app.get('/transferRequest', (_req, res) => {
    // TODO get all transferRequests

    // should allow query params for pagination and filtering by live/finished

    res.status(501).send();
  });

  app.post('/transferRequest', async (req, res) => {
    const { patient_id, transfer_to } = req.body;

    const transfer_request = await initialize_transfer_request(
      patient_id,
      transfer_to,
    );

    res.status(200).type('json').send(transfer_request);
  });

  app.get('/transferRequest/:transferRequestId', (_req, res) => {
    // TODO get transferRequest by ID

    res.status(501).send();
  });

  app.get('/patient/:patientId/transferRequest', (_req, res) => {
    // TODO get all transferRequests for a patient

    // should allow query params for pagination and filtering by live/finished

    res.status(501).send();
  });

  app.use(expressErrorHandler);

  return app;
};
