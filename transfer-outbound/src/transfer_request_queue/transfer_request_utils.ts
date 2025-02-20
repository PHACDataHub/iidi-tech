import type { transferCode } from 'src/types.d.ts';

import { get_queue } from './get_queue.ts';

export type transferRequestJob = Exclude<
  Awaited<ReturnType<ReturnType<typeof get_queue>['getJob']>>,
  undefined
>;

export const initialize_transfer_request = async (
  patient_id: string,
  transfer_to: transferCode,
) => {
  return get_queue().add(
    'transfer',
    {
      patient_id,
      transfer_to,
      stage: 'pending',
      stage_history: [],
    },
    {
      deduplication: { id: patient_id },
    },
  );
};

export const get_transfer_request_by_id = async (id: string) =>
  get_queue().getJob(id);

export const get_transfer_requests = async (
  start: number | undefined,
  end: number | undefined,
) => get_queue().getJobs(undefined, start, end);

export const get_transfer_request_job_info = async (
  transfer_request_job: transferRequestJob,
) => {
  const state = await transfer_request_job.getState();

  const { failedReason: failed_reason, finishedOn: finished_on } =
    transfer_request_job;

  const { patient_id, transfer_to, stage } = transfer_request_job.data;

  return {
    state,
    finished_on,
    failed_reason,
    patient_id,
    transfer_to,
    stage,
  };
};
