import { setTimeout } from 'node:timers/promises';

import { Worker, QueueEvents, Job } from 'bullmq';

import {
  get_patient_bundle_for_transfer,
  add_replaced_by_link_to_transfered_patient,
} from 'src/fhir_utils.ts';

import { post_bundle_to_inbound_transfer_service } from 'src/transfer_inbound_utils.ts';

import { get_connection_options } from './queue_utils.ts';
import {
  get_transfer_queue,
  assert_is_transfer_job,
  get_transfer_request_by_id,
  get_transfer_request_job_info,
} from './transfer_request_utils.ts';
import type { transferRequestJob } from './transfer_request_utils.ts';

import {
  is_non_terminal_stage,
  get_next_stage,
} from './transfer_stage_utils.ts';

import type { transferRequest } from './transferRequest.js';

const get_job_id = (job: transferRequestJob) => {
  // job id's should never be undefined during the work loop, this is just for type narrowing
  if (job.id === undefined) {
    throw new Error(
      'Attempting to process a transfer request job with a missing ID. This should never happen.',
    );
  } else {
    return job.id;
  }
};

const work_on_transfer_job = async (job: transferRequestJob) => {
  // NOTE: breaking the job in to work stages similar to a pattern mentioned here https://docs.bullmq.io/patterns/process-step-jobs,
  // note that while the job doesn't return to the queue between stages it does update the job data to track progress which will
  // allow it to pick back up from the last stage if it is failed/moved back to the queue for any reason. Each stage also includes
  // async work, so a worker won't be blocking on the node thread (express should still be able to handle requests, multiple jobs
  // could be processing, etc).
  // Could try a more complicated use of BullMQ, either spawning child jobs for each stage or using the flow concept, but both of those
  // add a good bit more complexity than we may need. The biggest trade off of the current approach, AFAIK, is that the stages all share
  // the same "attempts" count, so we can't fine tune the number of retries per-stage. Child jobs/a job flow would enable that
  while (is_non_terminal_stage(job.data.stage)) {
    // TODO for this and all other logging found here, switch to a good struct log approach. These simple logs are placeholders/for dev
    console.log(`Job ID ${job.id}: starting stage "${job.data.stage}"`);

    let next_stage = get_next_stage(job.data.stage);

    if (job.data.stage === 'collecting_and_transfering') {
      const bundle = await get_patient_bundle_for_transfer(job.data.patient_id);

      const transfer_response = await post_bundle_to_inbound_transfer_service(
        bundle,
        job.data.transfer_to,
      );

      const json = await transfer_response.json().catch(() => null);

      if (transfer_response.ok) {
        if (
          typeof json === 'object' &&
          json !== null &&
          'patient' in json &&
          typeof json.patient === 'object' &&
          json.patient !== null &&
          'id' in json.patient &&
          typeof json.patient.id === 'string'
        ) {
          await job.updateData({
            ...job.data,
            new_patient_id: json.patient.id,
          });
        } else {
          console.warn(
            `Job ID ${job.id}: (patient "${job.data.patient_id}" to "${job.data.transfer_to}") received` +
              `an ok response from the inbound system, but did not receive "patient.id" in the response body.` +
              `The transfer process will continue, but the outbound system's reference to the new patient will be incomplete`,
          );
        }
      } else {
        const base_error_message =
          `Job ID ${job.id}: inbound-transfer service for "${job.data.transfer_to}" responded to` +
          `patient ID "${job.data.patient_id}" transfer with a "${transfer_response.status}" status.`;

        const is_non_timing_client_error_status =
          /4[0-9][0-9]/.test(transfer_response.status.toString()) &&
          ![408, 429].includes(transfer_response.status); // timeout and too many request errors are worth retrying

        if (is_non_timing_client_error_status) {
          // Handle explicit rejection of the transfer request with an explicit state rather than letting an error throw,
          // don't want the queue's failure handling/retry logic hammering the transfer endpoint with known-bad request attempts
          next_stage = 'rejected';

          const rejection_reason =
            base_error_message +
            (typeof json === 'object' && json !== null && 'error' in json
              ? JSON.stringify(json)
              : 'Rejection reason not provided.');

          console.error(rejection_reason);

          await job.updateData({
            ...job.data,
            rejection_reason,
          });
        } else {
          throw new Error(base_error_message);
        }
      }
    } else if (job.data.stage === 'setting_patient_post_transfer_metadata') {
      // NOTE: vital assumption: this end point returns 200 IF AND ONLY IF the bundle was accepted and fully written to the receiving
      // FHIR server. Not a big ask, just have to hold to that or else the rollback handling won't work and data integrity is lost
      await add_replaced_by_link_to_transfered_patient(
        job.data.patient_id,
        get_job_id(job),
        job.data.transfer_to,
        job.data.new_patient_id,
      );
    }

    console.log(
      `Job ID ${job.id}: completed stage "${job.data.stage}, moving to next stage "${next_stage}"`,
    );

    await job.updateData({
      ...job.data,
      completed_stages: [...job.data.completed_stages, job.data.stage],
      stage: next_stage,
    });
  }

  console.log(
    `Job ID ${job.id}: finished on terminal stage "${job.data.stage}"`,
  );

  return job.data;
};

const handle_failed_transfer_request_job = async (
  failed_job: transferRequestJob,
) => {
  console.log(
    `Job ID ${failed_job.id}: failed on stage "${failed_job.data.stage}" having completed stages [${failed_job.data.completed_stages.join(', ')}]`,
  );

  const transfer_completed = failed_job.data.completed_stages.includes(
    'collecting_and_transfering',
  );

  const post_transfer_metadata_was_set =
    failed_job.data.completed_stages.includes(
      'setting_patient_post_transfer_metadata',
    );

  if (transfer_completed && !post_transfer_metadata_was_set) {
    if (failed_job.attemptsMade <= (failed_job.opts.attempts ?? 3) + 3) {
      const next_delay =
        Math.pow(2, failed_job.attemptsMade - 1) *
        (failed_job.opts.delay ?? 1000);

      console.log(
        `Job ID ${failed_job.id} failure handling: failed post-transfer to inbound PT, unable to roll back. Attempting to continue from last stage (${failed_job.data.stage}) in ${next_delay} milliseconds"`,
      );

      // unfortunately, it doesn't seem like there's a good way to retry _with_ delay directly on the queue. This retry attempt isn't
      // persisted to the queue till after this timeout passes on the worker server, which may be interupted if the server is killed or dies.
      // TODO: take a second look through the BullMQ docs, just in case. It'd be more failure-proof if this retry could be directly queued _with_ delay
      await setTimeout(next_delay);

      await failed_job.retry();
    } else {
      console.error(
        `Job ID ${failed_job.id} failure handling: failed post-transfer to inbound PT, unable to roll back. Still unable to continue after ${failed_job.attemptsMade} attemps, aborting. Data integrity risk!"`,
      );
    }
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
    // IMPORTANT: if the auto-job removal is ever configured to remove failed state job history, this may not find anything.
    // See error state below. If auto-job removal for failed state jobs is enabled, it should allow a suitable window for failure event handling attempts.
    const failed_job = await get_transfer_request_by_id(jobId);

    if (failed_job === undefined) {
      console.error(
        `Unable to ensure possible intermediate state is rolled back for failed event associated with job ID "${jobId}", no such job found.
        If "${jobId}" was a transfer request, data integrity can not be guaranteed for it!
        Auto-job removal may be overtuned on failed jobs, try increasing job retention.`,
      );
    } else {
      let is_transfer_job = null;
      try {
        assert_is_transfer_job(failed_job);
        is_transfer_job = true;
      } catch {
        is_transfer_job = false;
      }

      if (is_transfer_job) {
        const info = await get_transfer_request_job_info(failed_job);
        console.log(JSON.stringify(info, null, 2));

        await handle_failed_transfer_request_job(failed_job);
      }
    }
  });
};
