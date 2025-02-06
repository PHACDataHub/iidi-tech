import _ from 'lodash';
import request from 'supertest';

import {
  expected_age_groups,
  expected_jurisdictions,
  expected_sexes,
} from './aggregation_validation_utils.ts';
import { create_app } from './create_app.ts';

const valid_sample_data = [
  {
    AgeGroup: expected_age_groups[0],
    Count: 3,
    DoseCount: 4,
    Jurisdiction: expected_jurisdictions[0],
    ReferenceDate: '2025-02-05',
    OccurenceYear: '2025',
    Sex: expected_sexes[0],
  },
  {
    AgeGroup: expected_age_groups[_.random(1, expected_age_groups.length - 1)],
    Count: 4,
    DoseCount: 7,
    Jurisdiction: expected_jurisdictions[0],
    ReferenceDate: '2025-03-06',
    OccurenceYear: '2024',
    Sex: expected_sexes[_.random(1, expected_sexes.length - 1)],
  },
];

describe('create_app', () => {
  describe('/healthcheck', () => {
    it('Returns a 200 when the server is running', async () => {
      const app = await create_app();

      const response = await request(app).get('/healthcheck').send();

      expect(response.statusCode).toEqual(200);
    });
  });

  describe('/aggregated-data', () => {
    const ORIGINAL_ENV = process.env;

    beforeEach(() => {
      jest.resetModules();
    });
    afterEach(() => {
      process.env = ORIGINAL_ENV;
      fetchMock.resetMocks();
    });

    it('Returns merged data from across endpoints derived from the AGGREGATOR_URLS env var', async () => {
      const pt_1_test_url = 'https://pt-1/aggregator';
      const pt_1_test_response_data = valid_sample_data;

      const pt_2_test_url = 'https://pt-2/aggregator';
      const pt_2_test_response_data = [
        { ...valid_sample_data[0], Jurisdiction: expected_jurisdictions[1] },
        { ...valid_sample_data[1], Jurisdiction: expected_jurisdictions[1] },
      ];

      const test_urls = [pt_1_test_url, pt_2_test_url];

      fetchMock.mockIf(
        ({ url }) => test_urls.some((test_url) => url.startsWith(test_url)),
        async ({ url }) =>
          JSON.stringify(
            url.startsWith(pt_1_test_url)
              ? pt_1_test_response_data
              : pt_2_test_response_data,
          ),
      );

      process.env = {
        ...ORIGINAL_ENV,
        AGGREGATOR_URLS: test_urls.join(','),
      };

      const app = await create_app();

      const response = await request(app).get('/aggregated-data').send();

      expect(response.statusCode).toEqual(200);

      // comparing received and expected data with a set difference operation, as order doesn't matter
      const difference_between_expected_and_received_data = _.differenceWith(
        [...pt_1_test_response_data, ...pt_2_test_response_data],
        response.body.data as typeof pt_1_test_response_data,
        (expected_data, received_data) =>
          _.reduce(
            expected_data,
            (comparison_accumulator, value, key) =>
              comparison_accumulator &&
              received_data[key as keyof typeof expected_data] === value,
            true,
          ),
      );
      expect(difference_between_expected_and_received_data).toEqual([]);

      expect(response.body.errors).toEqual([]);
    });

    it('Handles errors per-endpoint, returns what data it can alongside any error messages', async () => {
      const pt_1_test_url = 'https://pt-1/aggregator';
      const pt_1_test_response_data = valid_sample_data;

      const pt_2_test_url = 'https://pt-2/aggregator';
      const pt_2_test_response_data_invalid = [
        { ...valid_sample_data[0], Jurisdiction: 'dasfadsf' },
        { ...valid_sample_data[1], Jurisdiction: 'asdfdsaf' },
      ];

      const pt_3_test_url = 'https://pt-3/aggregator';

      const test_urls = [pt_1_test_url, pt_2_test_url, pt_3_test_url];

      fetchMock.mockIf(
        ({ url }) => test_urls.some((test_url) => url.startsWith(test_url)),
        async ({ url }) => {
          if (url.startsWith(pt_1_test_url)) {
            return JSON.stringify(pt_1_test_response_data);
          } else if (pt_2_test_url) {
            return JSON.stringify(pt_2_test_response_data_invalid);
          } else {
            throw new Error('Some error');
          }
        },
      );

      process.env = {
        ...ORIGINAL_ENV,
        AGGREGATOR_URLS: test_urls.join(','),
      };

      const app = await create_app();

      const response = await request(app).get('/aggregated-data').send();

      expect(response.statusCode).toEqual(500);

      // comparing received and expected data with a set difference operation, as order doesn't matter
      const difference_between_expected_and_received_data = _.differenceWith(
        pt_1_test_response_data,
        response.body.data as typeof pt_1_test_response_data,
        (expected_data, received_data) =>
          _.reduce(
            expected_data,
            (comparison_accumulator, value, key) =>
              comparison_accumulator &&
              received_data[key as keyof typeof expected_data] === value,
            true,
          ),
      );
      expect(difference_between_expected_and_received_data).toEqual([]);

      expect(response.body.errors).toHaveLength(2);
    });
  });
});
