import type { Job } from 'bullmq';

import type { transferCode } from 'src/transfer_code_utils.ts';

import { get_queue } from './queue_utils.ts';
import { initial_stage } from './transfer_stage_utils.ts';
import type { transferRequest } from './transferRequest.js';

export const get_transfer_queue = () =>
  get_queue<transferRequest, transferRequest>('transfer-request-queue');

export type transferRequestJob = Exclude<
  Awaited<ReturnType<ReturnType<typeof get_transfer_queue>['getJob']>>,
  undefined
>;

export const transfer_job_name = 'transfer';
export const initialize_transfer_request = async (
  patient_id: string,
  transfer_to: transferCode,
) =>
  get_transfer_queue().add(
    transfer_job_name,
    {
      patient_id,
      transfer_to,
      stage: initial_stage,
      completed_stages: [],
    },
    {
      // IMPORTANT: this is effectively our transfer-lock mechanism, important that a patient can't have more than one active
      // transfer request at a time (and if the transfer succeeds, assume the patient resource is updated in such a way as
      // to no longer be considered valid to queue a transfer job for)
      deduplication: { id: patient_id },
    },
  );

export function assert_is_transfer_job(
  job: Job,
): asserts job is transferRequestJob {
  // TODO assert job.data shape too?
  if (
    job === null ||
    typeof job !== 'object' ||
    !('name' in job) ||
    job.name !== transfer_job_name
  ) {
    throw new Error(`Expected a "${transfer_job_name}" type job`);
  }
}

export const get_transfer_request_by_id = async (id: string) =>
  get_transfer_queue().getJob(id);

export const get_transfer_requests = async (
  start: number | undefined,
  end: number | undefined,
) => get_transfer_queue().getJobs(undefined, start, end);

export const get_transfer_request_job_info = async (
  transfer_request_job: transferRequestJob,
) => {
  const state = await transfer_request_job.getState();

  const { failedReason: failed_reason, finishedOn: finished_on } =
    transfer_request_job;

  const {
    patient_id,
    new_patient_id,
    transfer_to,
    stage,
    completed_stages,
    rejection_reason,
  } = transfer_request_job.data;

  return {
    job_id: transfer_request_job.id,
    state,
    finished_on,
    failed_reason,
    patient_id,
    new_patient_id,
    transfer_to,
    stage,
    completed_stages,
    rejection_reason,
  };
};
