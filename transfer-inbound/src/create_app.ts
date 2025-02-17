import express from 'express';

import { get_env } from './env.ts';
import { expressErrorHandler } from './error_utils.ts';

export const create_app = async () => {
  const { FHIR_URL } = get_env();

  // TODO delete later, just here so the TS compiler doesn't complain about FHIR_URL being unused.
  // I want the get_env import and usage demonstrated here, which is why I'm leaving it in when it's not
  // yet used
  console.log(`FHIR_URL: ${FHIR_URL}`);

  const app = express();

  // we'll need to be able to read `X-Forwarded-*` headers, both in prod and when using the dev docker setup
  app.set('trust proxy', true);

  app.use(express.json()); // parses JSON body payloads, converts req.body from a string to object
  app.use(express.urlencoded({ extended: false })); // parses URL-encoded payload parameters on POST/PUT in to req.body fields

  app.get('/healthcheck', (_req, res) => {
    // TODO consider if a non-trivial healthcheck is appropriate/useful
    res.status(200).send();
  });

  // TODO service-specific-endpoints-go-here

  app.use(expressErrorHandler);

  return app;
};
