import express from 'express';

import { get_env } from './env.ts';
import { expressErrorHandler } from './error_utils.ts';

export const create_app = async () => {
  const { FHIR_URL } = get_env();

  console.log(FHIR_URL); // TODO delete later, just here to stop TS compiler complaining about unused var

  const app = express();

  // we'll need to be able to read `X-Forwarded-*` headers, both in prod and when using the dev docker setup
  app.set('trust proxy', true);

  app.use(express.json()); // parses JSON body payloads, converts req.body from a string to object
  app.use(express.urlencoded({ extended: false })); // parses URL-encoded payload parameters on POST/PUT in to req.body fields

  app.get('/healthcheck', (_req, res) => {
    // TODO consider if a non-trivial healthcheck is appropriate/useful
    res.status(200).send();
  });

  /* transferRequest type to look something like:
    {
      id: string, // unique ID of the transferRequests entity
      patient: patientId,
      transfer_to: inboundPtId, // for the demo state, "ON" | "BC", minus the Id of the province this outbound API belongs to
      // `stage` TBD, currently thinking to use a task queue for processing with stages along these lines
      // Using a proper queue and processing microservices could be a follow up time permitting, but handle it in-server for now
      stage: "initializing" | "collecting" | "marking_transfered" | "transfering" | "done" | "rejecting" | "rejected"
      stage_history: [stage], // array of prior stage values for this transfer. Used for things like, when rejecting, knowing if transfer marks need to be reverted
      collected_records?: string, // stringified JSON blob of records to be transfered, 
      rejection_message?: string, // error that caused the rejection
    }
  */

  app.get('/transferRequest/', (_req, res) => {
    // TODO get all transferRequests

    // should allow query params for pagination and filtering by live/finished

    res.status(501).send();
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

  app.post('/patient/:patientId/transferRequest', (_req, res) => {
    // TODO create new transferRequest for a patient

    // should be assumed to only accept a subset of the transferRequest spec, just `patient` and `transfer_to`

    res.status(501).send();
  });

  app.use(expressErrorHandler);

  return app;
};
