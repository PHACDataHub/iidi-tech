import { get_env } from './env.ts';

import type { transferCode } from './transfer_code_utils.ts';
import type { bundle } from './types.d.ts';

export const post_bundle_to_inbound_transfer_service = async (
  bundle: bundle,
  transfer_to: transferCode,
) => {
  const { INBOUND_TRANSFER_SERVICES_BY_TRANSFER_CODE } = get_env();

  return fetch(
    `${INBOUND_TRANSFER_SERVICES_BY_TRANSFER_CODE[transfer_to]}/inbound-transfer`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ bundle }),
    },
  );
};
