import request from 'supertest';

import { create_app } from './create_app.ts';

const mockFhirStatus = jest.fn();
const mockRedisPing = jest.fn();

jest.mock('./fhir_utils.ts', () => ({
  is_fhir_status_active: () => mockFhirStatus(),
}));

jest.mock('./transfer_request_queue/transfer_request_utils.ts', () => ({
  get_transfer_queue: () => ({
    client: Promise.resolve({
      ping: () => mockRedisPing(),
    }),
  }),
}));

describe('create_app', () => {
  describe('/healthcheck', () => {
    it('Returns a 200 when the server is running', async () => {
      mockFhirStatus.mockResolvedValue(true);
      mockRedisPing.mockResolvedValue('PONG');

      const app = await create_app();
      const response = await request(app).get('/healthcheck').send();

      expect(response.statusCode).toEqual(200);
      expect(response.body).toEqual({
        is_fhir_active: true,
        redisStatus: 'CONNECTED',
      });
    });

    it('Returns 503 when FHIR is down', async () => {
      mockFhirStatus.mockResolvedValue(false);
      mockRedisPing.mockResolvedValue('PONG');

      const app = await create_app();
      const response = await request(app).get('/healthcheck').send();

      expect(response.statusCode).toEqual(503);
      expect(response.body).toEqual({
        is_fhir_active: false,
        redisStatus: 'CONNECTED',
      });
    });

    it('Returns 503 when Redis is down', async () => {
      mockFhirStatus.mockResolvedValue(true);
      mockRedisPing.mockRejectedValue(new Error('Redis connection failed'));

      const app = await create_app();
      const response = await request(app).get('/healthcheck').send();

      expect(response.statusCode).toEqual(503);
      expect(response.body).toEqual({
        is_fhir_active: true,
        redisStatus: 'DOWN',
      });
    });
  });
});
