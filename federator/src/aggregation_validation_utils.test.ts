import _ from 'lodash';

import {
  is_valid_aggregated_data,
  expected_jurisdictions,
  expected_sexes,
} from './aggregation_validation_utils.ts';

const valid_sample_data = [
  {
    Age: '1 year',
    Count: 3,
    Dose: 4,
    Jurisdiction: expected_jurisdictions[0],
    ReferenceDate: '2025-02-05',
    OccurrenceYear: '2025',
    Sex: expected_sexes[0],
  },
  {
    Age: '100 years',
    Count: 4,
    Dose: 7,
    Jurisdiction:
      expected_jurisdictions[_.random(1, expected_jurisdictions.length - 1)],
    ReferenceDate: '2025-03-06',
    OccurrenceYear: '2024',
    Sex: expected_sexes[_.random(1, expected_sexes.length - 1)],
  },
];

describe('is_valid_aggregated_data', () => {
  it('Returns true if all provided data matches the expected response of an aggregator API', () => {
    const trivial_passing_case = is_valid_aggregated_data([]);
    expect(trivial_passing_case).toBe(true);

    const non_trivial_passing_case =
      is_valid_aggregated_data(valid_sample_data);
    expect(non_trivial_passing_case).toBe(true);
  });

  it('Returns false if any provided data does not match the expected response of an aggregator API', () => {
    const sample_with_invalid_age_group = [
      ...valid_sample_data,
      { ...valid_sample_data[0], Age: -1 },
    ];
    expect(is_valid_aggregated_data(sample_with_invalid_age_group)).toBe(false);

    const sample_with_invalid_count = [
      ...valid_sample_data,
      { ...valid_sample_data[0], Count: 'fadsfasf' },
    ];
    expect(is_valid_aggregated_data(sample_with_invalid_count)).toBe(false);

    const sample_with_invalid_dose_count = [
      ...valid_sample_data,
      { ...valid_sample_data[0], Dose: -1 },
    ];
    expect(is_valid_aggregated_data(sample_with_invalid_dose_count)).toBe(
      false,
    );

    const sample_with_invalid_jurisdiction = [
      ...valid_sample_data,
      { ...valid_sample_data[0], Jurisdiction: -1 },
    ];
    expect(is_valid_aggregated_data(sample_with_invalid_jurisdiction)).toBe(
      false,
    );

    const sample_with_invalid_reference_date_format = [
      ...valid_sample_data,
      { ...valid_sample_data[0], ReferenceDate: '2025/22/02' },
    ];
    expect(
      is_valid_aggregated_data(sample_with_invalid_reference_date_format),
    ).toBe(false);

    const sample_with_invalid_occurence_year_format = [
      ...valid_sample_data,
      { ...valid_sample_data[0], ReferenceDate: '2025/22/02' },
    ];
    expect(
      is_valid_aggregated_data(sample_with_invalid_occurence_year_format),
    ).toBe(false);

    const sample_with_invalid_sex = [
      ...valid_sample_data,
      { ...valid_sample_data[0], Sex: 'fadsfasf' },
    ];
    expect(is_valid_aggregated_data(sample_with_invalid_sex)).toBe(false);
  });
});
