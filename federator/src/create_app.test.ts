import request from 'supertest';

import { create_app } from './create_app.ts';

describe('create_app', () => {
  describe('/healthcheck', () => {
    it('Returns a 200 when the server is running', async () => {
      const app = await create_app();

      const response = await request(app).get('/healthcheck').send();

      expect(response.statusCode).toEqual(200);
    });
  });
});
