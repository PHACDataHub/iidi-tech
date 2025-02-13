import { randomUUID } from 'crypto';

export type transferStage =
  | 'initializing'
  | 'collecting'
  | 'marking_transfered'
  | 'transfering'
  | 'done'
  | 'rejecting'
  | 'rejected';

export interface transferRequest {
  id: string;
  patient_id: string;
  transfer_to: 'ON' | 'BC';
  // `stage` TBD, currently thinking to use a task queue for processing with stages along these lines
  // Using a proper task queue and persistence mechanism, maybe separate microservices for processing, could be a follow up time permitting,
  // but handle it all in-memory for initial minimal viable implementation
  stage: transferStage;
  stage_history: transferStage[];
  rejection_message?: string; // error that caused the rejection
}

// TODO query for `id` in storage layer
export const get_transfer_request_by_id = async (
  _id: string,
): Promise<transferRequest | null> => null;

export const get_unused_transfer_id = async (): Promise<string> => {
  // entropy should be sufficiently high enough to avoid collisions, even without the `{ disableEntropyCache: true }`
  // option. Don't really expect to need to make more than one try to get an unused key, but it's not expensive to be
  // safe here
  const id = randomUUID();

  const transfer_request_already_using_id =
    await get_transfer_request_by_id(id);

  if (transfer_request_already_using_id === null) {
    return id;
  } else {
    return get_unused_transfer_id();
  }
};

export const initialize_transfer_request = async (
  patient_id: string,
  transfer_to: 'ON' | 'BC',
): Promise<transferRequest> => {
  // TODO validate arguments, throw AppError on rejection

  const id = await get_unused_transfer_id();

  const transfer_request = {
    id,
    patient_id,
    transfer_to,
    stage: 'initializing',
    stage_history: [],
  } as transferRequest;

  // TODO write to storage layer/task queue

  return transfer_request;
};
