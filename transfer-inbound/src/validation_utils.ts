import { AppError } from './error_utils.ts';
import type { Bundle } from './types.js';

export function assert_bundle_follows_business_rules(
  _bundle: unknown,
): asserts _bundle is Bundle {
  // TODO validate buisness logic rules for transfer bundle (e.g. exactly one patient record,
  // no unexpected record types or out of scope fields, etc)
  // Throw a descriptive AppError if validation fails

  throw new AppError(501, 'Business logic validation not implemented');
}
