import type { transferCode } from 'src/types.d.ts';

export type transferStage =
  | 'collecting'
  | 'marking_transfered'
  | 'transfering'
  | 'finalizing'
  | 'rejecting';

export interface transferRequest {
  patient_id: string;
  transfer_to: transferCode;
  // `stage` TBD, currently thinking to use a task queue for processing with stages along these lines
  // Using a proper task queue and persistence mechanism, maybe separate microservices for processing, could be a follow up time permitting,
  // but handle it all in-memory for initial minimal viable implementation
  stage: transferStage;
  stage_history: transferStage[];
}
