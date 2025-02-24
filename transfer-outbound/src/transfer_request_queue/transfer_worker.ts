import { Worker, QueueEvents, Job } from 'bullmq';

import {
  get_patient_bundle_for_transfer,
  mark_patient_transfered,
  unmark_patient_transfered,
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

import { terminal_stage, get_next_stage } from './transfer_stage_utils.ts';

import type { transferRequest } from './transferRequest.js';

const work_on_transfer_job = async (job: transferRequestJob) => {
  // NOTE: breaking the job in to work stages similar to a pattern mentioned here https://docs.bullmq.io/patterns/process-step-jobs,
  // note that while the job doesn't return to the queue between stages it does update the job data to track progress which will
  // allow it to pick back up from the last stage if it is failed/moved back to the queue for any reason. Each stage also includes
  // async work, so a worker won't be blocking on the node thread (express should still be able to handle requests, multiple jobs
  // could be processing, etc).
  // Could try a more complicated use of BullMQ, either spawning child jobs for each stage or using the flow concept, but both of those
  // add a good bit more complexity than we may need. The biggest trade off of the current approach, AFAIK, is that the stages all share
  // the same "attempts" count, so we can't fine tune the number of retries per-stage. Child jobs/a job flow would enable that
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
      // NOTE: vital assumption: this end point returns 200 IF AND ONLY IF the bundle was accepted and fully written to the receiving
      // FHIR server. Not a big ask, just have to hold to that or else the rollback handling won't work and data integrity is lost
      const response = await post_bundle_to_inbound_transfer_service(
        job.data.bundle,
        job.data.transfer_to,
      );
      // TODO handle response, if it's a 200 then expect a new patient ID, if anything else then throw
      console.log(response);
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

const handle_failed_transfer_request_job = async (
  failed_job: transferRequestJob,
) => {
  const transfer_marks_were_created =
    failed_job.data.completed_stages.includes('marking_transfered');

  const transfer_completed =
    failed_job.data.completed_stages.includes('transfering');

  const transfer_finalized =
    failed_job.data.completed_stages.includes('finalizing');

  if (
    (transfer_finalized &&
      !(transfer_marks_were_created || transfer_completed)) ||
    (transfer_completed && !transfer_marks_were_created)
  ) {
    // TODO unexpected combinations, should not be reachable, something really went wrong
    // log and _maybe_ attempt unmark if applicable
  }

  if (!transfer_marks_were_created) {
    // TODO clean failure, log and exit
  } else if (transfer_marks_were_created && !transfer_completed) {
    // TODO log failure case

    await unmark_patient_transfered(
      failed_job.data.patient_id,
      failed_job.data.transfer_to,
      failed_job.id,
    );

    // TODO log successful unmarking
  } else if (
    transfer_marks_were_created &&
    transfer_completed &&
    !transfer_finalized
  ) {
    // Too late to stop, transfer already accepted on inbound end, must have failed during finalizing step. Retry for
    // data integrity sake.
    // TODO check number of attempts, maybe give up evetually with an appropriately serious log
    await failed_job.retry();
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
    // TODO confirm understanding of queue level failed events. If I understand correctly, this is esentially a worker on a
    // queue for global failure messages, so we should have all the resiliancy benefits of a queue behind this cleanup stage
    // ... but what if the handler of a failure event fails? Does it still get three attempts? Does it trigger a second-level
    // `failed` event we might have to handle here?
    // Also, as noted below, is is treated as a child of the original failed job or otherwise prevent the failed job from
    // being pruned from the failed queue? Recovery requires that we can get the state of the failing ID still, but this event
    // only receives its ID, so hopefully we can still look it up

    const failed_job = await get_transfer_request_by_id(jobId);

    if (failed_job === undefined) {
      // TODO want to ensure this never happens! Look further in to how the failed events are processed,
      // whether a failed job can be pruned before it's failed event is complete
      console.error(
        `Unable to ensure possible intermediate state is rolled back for failed event "${jobId}", no such job found`,
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
        // TODO conform with logging patern (logging patern TBD)
        const info = await get_transfer_request_job_info(failed_job);
        console.log(JSON.stringify(info, null, 2));

        await handle_failed_transfer_request_job(failed_job);
      }
    }
  });
};
