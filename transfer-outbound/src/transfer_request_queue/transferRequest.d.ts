import type { transferCode } from 'src/transfer_code_utils.ts';
import type { bundle } from 'src/types.d.ts';

import type { transferStage } from './transfer_stage_utils.ts';

export interface transferRequest {
  patient_id: string;
  transfer_to: transferCode;
  stage: transferStage;
  completed_stages: transferStage[];
  bundle?: bundle;
}
