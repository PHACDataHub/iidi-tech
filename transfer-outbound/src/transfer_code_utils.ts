export const transfer_codes = ['BC', 'ON'] as const;

export type transferCode = (typeof transfer_codes)[number];

export const is_transfer_code = (
  transfer_code: unknown,
): transfer_code is transferCode =>
  typeof transfer_code === 'string' &&
  transfer_codes.includes(transfer_code as transferCode);
