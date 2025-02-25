import { Queue } from 'bullmq';

import _ from 'lodash';

import { get_env } from 'src/env.ts';

export const get_connection_options = () => {
  const { REDIS_HOST, REDIS_PORT, REDIS_PASSWORD } = get_env();

  return {
    host: REDIS_HOST,
    port: REDIS_PORT,
    password: REDIS_PASSWORD,
  };
};

const get_queue_cached = _.memoize(
  <dataType, resultType>(
    queue_name: string,
    connection: {
      host: string;
      port: number;
      password: string;
    },
  ) =>
    new Queue<dataType, resultType>(queue_name, {
      connection,
      defaultJobOptions: {
        attempts: 3,
        backoff: {
          type: 'exponential',
          delay: 1000,
        },
      },
    }),
  (queue_name, connection) =>
    `${queue_name}-${connection.host}-${connection.port}-${connection.password}`,
);

export const get_queue = <dataType, resultType>(queue_name: string) => {
  return get_queue_cached<dataType, resultType>(
    queue_name,
    get_connection_options(),
  );
};
