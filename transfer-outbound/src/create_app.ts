import express from 'express';

import { expressErrorHandler } from './error_utils.ts';
import { query_param_to_int_or_undefined } from './request_utils.ts';

import {
  initialize_transfer_request,
  get_transfer_request_by_id,
  get_transfer_requests,
  get_transfer_request_job_info,
} from './transfer_request_queue/transfer_request_utils.ts';

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

  app.get('/transferRequest', async (req, res) => {
    const { start, end } = req.query;

    const jobs = await get_transfer_requests(
      query_param_to_int_or_undefined(start),
      query_param_to_int_or_undefined(end),
    );

    const jobs_info = await Promise.all(
      jobs.map(get_transfer_request_job_info),
    );

    res.status(200).send(jobs_info);
  });

  app.post('/transferRequest', async (req, res) => {
    const { patient_id, transfer_to } = req.body;

    const transfer_request = await initialize_transfer_request(
      patient_id,
      transfer_to,
    );

    res
      .status(200)
      .type('json')
      .send({ transfer_request_id: transfer_request.id });
  });

  app.get('/transferRequest/:transferRequestId', async (req, res) => {
    const transfer_request_job = await get_transfer_request_by_id(
      req.params.transferRequestId,
    );

    if (transfer_request_job === undefined) {
      res.status(404).send();
    } else {
      const info = await get_transfer_request_job_info(transfer_request_job);
      res.status(200).send(info);
    }
  });

  app.get('/patient/:patientId/transferRequest', (_req, res) => {
    // TODO get all transferRequests for a patient

    // should allow query params for pagination and filtering by live/finished

    res.status(501).send();
  });

  app.use(expressErrorHandler);

  return app;
};
