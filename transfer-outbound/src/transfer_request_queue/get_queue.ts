import { Queue } from 'bullmq';

import _ from 'lodash';

import { get_env } from 'src/env.ts';

import type { transferRequest } from './transferRequest.d.ts';

const get_queue_cached = _.memoize(
  (queue_name: string, host: string, port: number, password: string) =>
    new Queue<transferRequest, transferRequest>(queue_name, {
      connection: {
        host,
        port,
        password,
      },
    }),
  (queue_name: string, host: string, port: number, password: string) =>
    `${queue_name}-${host}-${port}-${password}`,
);

export const get_queue = (queue_name = 'transfer-request-queue') => {
  const { REDIS_PORT, REDIS_PASSWORD, REDIS_HOST } = get_env();

  return get_queue_cached(queue_name, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD);
};
