import _ from 'lodash';
import type { Writable } from 'type-fest';
import validator from 'validator';

export const expected_age_pattern =
  /(^1 year$)|(^[2-9] years$)|(^[1-9][0-9][0-9]? years$)|(^Unknown$)/;
export const expected_jurisdictions = ['BC', 'ON'] as const;
export const expected_sexes = ['Other', 'Female', 'Male'] as const;

export interface AggregationGroupedData {
  AgeGroup: '1 year' | `${number} years` | 'Unknown';
  Count: number;
  Dose: number;
  Jurisdiction: Writable<typeof expected_jurisdictions>[number];
  ReferenceDate: `${number}-${number}-${number}`;
  OccurrenceYear: number | 'Unknown';
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
          'Dose',
          'Jurisdiction',
          'ReferenceDate',
          'OccurrenceYear',
          'Sex',
        ]).length === 0 &&
        expected_age_pattern.test(data.AgeGroup) &&
        _.isInteger(data.Count) &&
        data.Count >= 0 &&
        _.isInteger(data.Dose) &&
        data.Dose >= 0 &&
        expected_jurisdictions.includes(data.Jurisdiction) &&
        validator.isDate(data.ReferenceDate, { format: 'YYYY-MM-DD' }) &&
        /^([1,2][0-9][0-9][0-9])|(Unknown)$/.test(data.OccurrenceYear) &&
        expected_sexes.includes(data.Sex),
    );
  }
};
