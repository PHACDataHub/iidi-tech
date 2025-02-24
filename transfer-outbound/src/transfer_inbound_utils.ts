import { get_env } from './env.ts';

import type { transferCode } from './transfer_code_utils.ts';
import type { bundle } from './types.d.ts';

export const post_bundle_to_inbound_transfer_service = async (
  bundle: bundle,
  transfer_to: transferCode,
) => {
  const { INBOUND_TRANSFER_SERIVCES_BY_TRANSFER_CODE } = get_env();

  return await fetch(
    `${INBOUND_TRANSFER_SERIVCES_BY_TRANSFER_CODE[transfer_to]}/inbound-transfer`,
    { method: 'post', body: JSON.stringify(bundle) },
  );
};
