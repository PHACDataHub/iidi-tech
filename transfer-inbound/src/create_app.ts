import express from 'express';

import { get_env } from './env.ts';
import { expressErrorHandler } from './error_utils.ts';

export const create_app = async () => {
  const { DEV_IS_LOCAL_ENV } = get_env();

  // TODO delete later, just here so the TS compiler doesn't complain about DEV_IS_LOCAL_ENV being unused.
  // I want the get_env import and usage demonstrated here, which is why I'm leaving it in when it's not
  // yet used
  console.log(`DEV_IS_LOCAL_ENV: ${DEV_IS_LOCAL_ENV}`);

  const app = express();

  // we'll need to be able to read `X-Forwarded-*` headers, both in prod and when using the dev docker setup
  app.set('trust proxy', true);

  app.use(express.json()); // parses JSON body payloads, converts req.body from a string to object
  app.use(express.urlencoded({ extended: false })); // parses URL-encoded payload parameters on POST/PUT in to req.body fields

  app.get('/healthcheck', (_req, res) => {
    // TODO consider if a non-trivial healthcheck is appropriate/useful
    res.send(200);
  });

  // TODO service-specific-endpoints-go-here

  app.use(expressErrorHandler);

  return app;
};
