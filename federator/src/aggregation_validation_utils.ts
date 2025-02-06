import _ from 'lodash';
import type { Writable } from 'type-fest';
import { isDate } from 'validator';

export const expected_age_groups = [
  '0-2 years',
  '3-5 years',
  '6-17 years',
  '18+ years',
  'Unknown',
] as const;
export const expected_jurisdictions = ['BC', 'ON'] as const;
export const expected_sexes = ['Other', 'Female', 'Male'] as const;

export interface AggregationGroupedData {
  AgeGroup: Writable<typeof expected_age_groups>[number];
  Count: number;
  DoseCount: number;
  Jurisdiction: Writable<typeof expected_jurisdictions>[number];
  ReferenceDate: `${number}-${number}-${number}`;
  Sex: Writable<typeof expected_sexes>[number];
}

export const is_valid_aggregated_data = (
  aggregated_data: unknown,
): aggregated_data is AggregationGroupedData[] => {
  if (!Array.isArray(aggregated_data)) {
    return false;
  } else {
    return aggregated_data.every(
      (data) =>
        _.difference(_.keys(data), [
          'AgeGroup',
          'Count',
          'DoseCount',
          'Jurisdiction',
          'ReferenceDate',
          'Sex',
        ]).length === 0 &&
        expected_age_groups.includes(data.AgeGroup) &&
        _.isInteger(data.Count) &&
        data.Count >= 0 &&
        _.isInteger(data.DoseCount) &&
        data.DoseCount >= 0 &&
        expected_jurisdictions.includes(data.Jurisdiction) &&
        isDate(data.ReferenceDate, { format: 'YYYY-MM-DD' }) &&
        expected_sexes.includes(data.Sex),
    );
  }
};
