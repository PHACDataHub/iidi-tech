import { setTimeout } from 'timers/promises';

import axios, { isAxiosError } from 'axios';

import { get_env } from './env.ts';
import { logger } from './logger.ts';

const { MAX_RETRIES, RETRY_DELAY } = get_env();

interface TransferJobResponse {
  job_id: string;
  state: string;
  finished_on: string | null;
  patient_id: string;
  new_patient_id: string | null;
  transfer_to: string;
  stage: string;
  completed_stages: string[];
  rejection_reason?: string;
}
export async function checkPatientExists(
  patientId: string,
  fhirUrl: string,
): Promise<boolean> {
  try {
    const response = await axios.get(`${fhirUrl}/Patient/${patientId}`);
    return response.status === 200;
  } catch (error) {
    if (isAxiosError(error)) {
      return false;
    }
    throw error;
  }
}

export async function waitForTransferCompletion(
  jobId: string,
  outboundUrl: string,
): Promise<TransferJobResponse> {
  let lastState = '';
  let lastStage = '';

  for (let i = 0; i < MAX_RETRIES; i++) {
    try {
      const response = await axios.get(
        `${outboundUrl}/transfer-request/${jobId}`,
      );

      if (response.status !== 200) {
        throw new Error(`Unexpected HTTP status: ${response.status}`);
      }

      const jobInfo = response.data as TransferJobResponse;
      lastState = jobInfo.state;
      lastStage = jobInfo.stage;

      logger.debug(`Job check attempt ${i + 1}/${MAX_RETRIES}`, {
        jobId,
        state: jobInfo.state,
        stage: jobInfo.stage,
      });

      if (jobInfo.state === 'completed') {
        if (jobInfo.stage === 'done') {
          if (!jobInfo.new_patient_id) {
            throw new Error('Completed job missing new_patient_id');
          }
          return jobInfo;
        }
        throw new Error(`Completed job has unexpected stage: ${jobInfo.stage}`);
      }

      logger.debug(`Unexpected state/stage: ${jobInfo.state}/${jobInfo.stage}`);
    } catch (error) {
      if (isAxiosError(error)) {
        if (error.response?.status === 404) {
          throw new Error(`Job ${jobId} not found`);
        }
        if (i === MAX_RETRIES - 1) {
          throw new Error(`Final attempt failed: ${error.message}`);
        }
      }
      if (error instanceof Error && !isAxiosError(error)) {
        throw error;
      }
    }

    await setTimeout(RETRY_DELAY);
  }

  throw new Error(
    `Job ${jobId} did not reach 'completed/done' after ${MAX_RETRIES} retries. ` +
      `Last state: ${lastState}, last stage: ${lastStage}`,
  );
}

export async function verifyTransferFailure(
  patientId: string,
  outboundUrl: string,
  targetProvince: string,
) {
  try {
    const response = await axios.post(`${outboundUrl}/transfer-request`, {
      patient_id: patientId,
      transfer_to: targetProvince,
    });

    throw new Error(
      `Unexpected success (${response.status}) for duplicate transfer`,
    );
  } catch (error) {
    if (!isAxiosError(error)) {
      throw new Error(`Error occured during failure verification: ${error}`);
    }

    if (error.response?.status !== 400) {
      throw new Error(`Expected 400, got ${error.response?.status}`);
    }

    const errorMessage = error.response.data?.error?.toLowerCase();
    if (!errorMessage?.includes('replaced by a newer patient record')) {
      throw new Error(
        'Missing expected error message in response for duplicate patient transfer',
      );
    }

    logger.info(`Validated transfer block for patient ${patientId}`);
  }
}
