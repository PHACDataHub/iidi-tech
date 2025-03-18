import request from 'supertest';

import { create_app } from './create_app.ts';
import { is_fhir_status_active } from './fhir_utils.ts';

jest.mock('./fhir_utils.ts', () => ({
  is_fhir_status_active: jest.fn(),
}));

describe('create_app', () => {
  describe('/healthcheck', () => {
    it('Returns a 200 when the FHIR server is active', async () => {
      (is_fhir_status_active as jest.Mock).mockResolvedValue(true);
      const app = await create_app();

      const response = await request(app).get('/healthcheck').send();

      expect(response.statusCode).toEqual(200);
    });

    it('Returns 503 when FHIR server is not active', async () => {
      (is_fhir_status_active as jest.Mock).mockResolvedValue(false);
      const app = await create_app();
      const response = await request(app).get('/healthcheck').send();
      expect(response.statusCode).toEqual(503);
    });
  });
});
