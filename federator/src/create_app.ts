import express from 'express';

import { is_valid_aggregated_data } from './aggregation_validation_utils.ts';
import type { AggregationGroupedData } from './aggregation_validation_utils.ts';
import { get_env } from './env.ts';
import { expressErrorHandler } from './error_utils.ts';

export const create_app = async () => {
  const { AGGREGATOR_URLS } = get_env();

  const app = express();

  // we'll need to be able to read `X-Forwarded-*` headers, both in prod and when using the dev docker setup
  app.set('trust proxy', true);

  app.use(express.json()); // parses JSON body payloads, converts req.body from a string to object
  app.use(express.urlencoded({ extended: false })); // parses URL-encoded payload parameters on POST/PUT in to req.body fields

  app.get('/healthcheck', (_req, res) => {
    // TODO consider if a non-trivial healthcheck is appropriate/useful
    res.status(200).send();
  });

  app.get('/aggregated-data', async (_req, res) => {
    const aggregator_results = await Promise.allSettled(
      AGGREGATOR_URLS.map(async (url) => {
        const aggregator_endpoint = `${url}/aggregated-data`;

        const response = await fetch(aggregator_endpoint);

        if (response.status === 200) {
          const aggregated_data = await response.json();

          if (is_valid_aggregated_data(aggregated_data)) {
            return aggregated_data;
          } else {
            throw new Error(
              `Aggregator at ${aggregator_endpoint} responded with incorrectly formatted data`,
            );
          }
        } else {
          throw new Error(
            `Aggregator at ${aggregator_endpoint} responded with non-200 code (${response.status})`,
          );
        }
      }),
    );

    const processed_aggregates = aggregator_results.reduce<{
      data: AggregationGroupedData[];
      errors: string[];
    }>(
      ({ data, errors }, result) =>
        result.status === 'fulfilled'
          ? { data: [...data, ...result.value], errors }
          : { data, errors: [...errors, result.reason.message] },
      { data: [], errors: [] },
    );

    res
      .type('json')
      .status(processed_aggregates.errors.length === 0 ? 200 : 500)
      .send(processed_aggregates);
  });

  app.use(expressErrorHandler);

  return app;
};
