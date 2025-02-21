import { Worker, QueueEvents, Job } from 'bullmq';

import { get_connection_options } from './queue_utils.ts';
import {
  get_transfer_queue,
  assert_is_transfer_job,
  get_transfer_request_by_id,
  get_transfer_request_job_info,
} from './transfer_request_utils.ts';
import type { transferRequestJob } from './transfer_request_utils.ts';

import {
  transfer_stages,
  terminal_stage,
  get_next_stage,
} from './transfer_stage_utils.ts';

import type { transferRequest } from './transferRequest.js';

const rollback_interupted_transfer_job = (_job: transferRequestJob) => {
  // TODO
};

const work_on_transfer_job = async (job: transferRequestJob) => {
  if (!transfer_stages.includes(job.data.stage)) {
    throw new Error(
      `Transfer request "${job.id}" reached an unknown stage "${job.data.stage}"`,
    );
  }

  while (job.data.stage !== terminal_stage) {
    // TODO work loop

    await job.updateData({
      ...job.data,
      stage_history: [...job.data.stage_history, job.data.stage],
      stage: get_next_stage(job.data.stage),
    });
  }

  return job.data;
};

export const initialize_transfer_worker = () => {
  const transferQueue = get_transfer_queue();

  const transferWorker = new Worker<transferRequest, transferRequest>(
    transferQueue.name,
    async (job: Job) => {
      assert_is_transfer_job(job);

      return work_on_transfer_job(job);
    },
    { connection: get_connection_options() },
  );

  transferWorker.on('error', (err) => {
    console.error(err);
  });

  const queueEvents = new QueueEvents(transferQueue.name, {
    connection: get_connection_options(),
  });
  queueEvents.on('failed', async ({ jobId }) => {
    const failed_job = await get_transfer_request_by_id(jobId);

    if (failed_job === undefined) {
      // TODO want to ensure this never happens!
      console.error(
        `Unable to ensure transfer state rollback for failed event "${jobId}", no such job found`,
      );
    } else {
      const info = await get_transfer_request_job_info(failed_job);
      console.log(JSON.stringify(info, null, 2));

      rollback_interupted_transfer_job(failed_job);
    }
  });
};
