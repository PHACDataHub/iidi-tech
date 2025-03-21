import type { transferCode } from 'src/transfer_code_utils.ts';

import type { transferStage } from './transfer_stage_utils.ts';

export interface transferRequest {
  initialized_on: number;
  patient_id: string;
  transfer_to: transferCode;
  stage: transferStage;
  completed_stages: transferStage[];
  new_patient_id?: string;
  rejection_reason?: string;
}
