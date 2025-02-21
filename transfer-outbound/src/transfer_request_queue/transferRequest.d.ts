import type { transferCode } from 'src/types.d.ts';

import type { transferStage } from './transfer_stage_utils.ts';

export interface transferRequest {
  patient_id: string;
  transfer_to: transferCode;
  stage: transferStage;
  stage_history: transferStage[];
}
