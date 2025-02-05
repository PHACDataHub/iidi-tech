import dotenv from 'dotenv';

import { create_app } from './create_app.ts';
import { get_env } from './env.ts';

dotenv.config({ path: '.env', override: true }); // relative to the call point, e.g. the service root

const { EXPRESS_HOST, EXPRESS_PORT } = get_env();

process.on('SIGTERM', () => {
  throw new Error('SIGTERM');
});
process.on('SIGINT', () => {
  throw new Error('SIGINT');
});

const app = await create_app();

app.listen({ host: EXPRESS_HOST, port: EXPRESS_PORT }, () =>
  console.log(`🚀 Federator API listening on ${EXPRESS_HOST}:${EXPRESS_PORT}`),
);
