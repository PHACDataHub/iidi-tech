import { Queue } from 'bullmq';

import _ from 'lodash';

import { get_env } from 'src/env.ts';

import type { transferRequest } from './transferRequest.js';

const get_queue_cached = _.memoize(
  <dataType, resultType>(
    queue_name: string,
    host: string,
    port: number,
    password: string,
  ) =>
    new Queue<dataType, resultType>(queue_name, {
      connection: {
        host,
        port,
        password,
      },
    }),
  (queue_name: string, host: string, port: number, password: string) =>
    `${queue_name}-${host}-${port}-${password}`,
);

export const get_queue = <dataType, resultType>(queue_name: string) => {
  const { REDIS_PORT, REDIS_PASSWORD, REDIS_HOST } = get_env();

  return get_queue_cached<dataType, resultType>(
    queue_name,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
  );
};

export const transfer_queue_name = 'transfer-request-queue';
export const get_transfer_queue = () =>
  get_queue<transferRequest, transferRequest>(transfer_queue_name);
