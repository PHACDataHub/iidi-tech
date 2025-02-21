import { Worker, QueueEvents, Job } from 'bullmq';

import {
  get_patient_bundle_for_transfer,
  mark_patient_transfered,
  unmark_patient_transfered,
} from 'src/fhir_utils.ts';

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

const work_on_transfer_job = async (job: transferRequestJob) => {
  if (!transfer_stages.includes(job.data.stage)) {
    throw new Error(
      `Transfer request "${job.id}" reached an unknown stage "${job.data.stage}"`,
    );
  }

  while (job.data.stage !== terminal_stage) {
    if (job.data.stage === 'collecting') {
      const bundle = await get_patient_bundle_for_transfer(job.data.patient_id);
      await job.updateData({
        ...job.data,
        bundle,
      });
    } else if (job.data.stage === 'marking_transfered') {
      await mark_patient_transfered(
        job.data.patient_id,
        job.data.transfer_to,
        job.id,
      );
    } else if (job.data.stage === 'transfering') {
      // TODO POST bundle to transfer-inbound
    } else if (job.data.stage === 'finalizing') {
      // TODO potentially circle back to add final confirmation mark, maybe the patient ID in the inbound system, to
      // the patient record in the outbound system
    }

    await job.updateData({
      ...job.data,
      completed_stages: [...job.data.completed_stages, job.data.stage],
      stage: get_next_stage(job.data.stage),
    });
  }

  return job.data;
};

const rollback_interupted_transfer_job = async (job: transferRequestJob) => {
  const transfer_marks_were_created =
    job.data.completed_stages.includes('marking_transfered');
  const transfer_did_not_complete =
    job.data.completed_stages.includes('transfering');
  if (transfer_marks_were_created && transfer_did_not_complete) {
    await unmark_patient_transfered(
      job.data.patient_id,
      job.data.transfer_to,
      job.id,
    );
  }
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

      await rollback_interupted_transfer_job(failed_job);
    }
  });
};
