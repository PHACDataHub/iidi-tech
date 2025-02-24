import { AppError } from './error_utils.ts';
import type { transferCode } from './transfer_code_utils.ts';

export function assert_patient_id_is_valid(
  patient_id: unknown,
): asserts patient_id is string {
  if (typeof patient_id !== 'string') {
    throw new AppError(
      400,
      `Invalid patient id, expected a string value, got "${patient_id}" (${typeof patient_id})`,
    );
  }

  const expected_pattern = /^[0-9]+$/;
  if (!expected_pattern.test(patient_id)) {
    throw new AppError(
      400,
      `Invalid patient id, expected to match pattern "${expected_pattern}", got: "${patient_id}"`,
    );
  }
}

export function assert_transfer_code_is_valid(
  transfer_code: unknown,
): asserts transfer_code is transferCode {
  // TODO refine this, should be single source of truth for transfer codes
  // might want the logic to reject self-transfers here too?
  const accepted_codes = ['BC', 'ON'];

  if (
    typeof transfer_code !== 'string' ||
    !accepted_codes.includes(transfer_code)
  ) {
    throw new AppError(
      400,
      `Invalid transfer code, expected "${accepted_codes.join(' | ')}", got: "${transfer_code}"`,
    );
  }
}
