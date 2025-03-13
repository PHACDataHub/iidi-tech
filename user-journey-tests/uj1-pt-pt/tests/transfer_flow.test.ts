import axios, { isAxiosError } from 'axios';

import { get_env } from './utils/env.ts';
import { logger } from './utils/logger.ts';
import {
  checkPatientExists,
  verifyTransferFailure,
  waitForTransferCompletion,
} from './utils/transfer_utils.ts';

const { ON_OUTBOUND_URL, BC_OUTBOUND_URL, ON_FHIR_URL, BC_FHIR_URL } =
  get_env();

function getRandomPatientId(totalPatients = 100): string {
  const randomIndex = Math.floor(Math.random() * totalPatients);
  return (1 + randomIndex * 3).toString();
}

async function testProvinceTransfer(
  sourceOutboundUrl: string,
  targetFhirUrl: string,
  targetProvince: string,
) {
  const patientId = getRandomPatientId();

  try {
    logger.info(
      `Testing transfer to ${targetProvince} for patient ${patientId}`,
    );

    // Initial transfer
    const transferResponse = await axios.post(
      `${sourceOutboundUrl}/transfer-request`,
      { patient_id: patientId, transfer_to: targetProvince },
    );

    if (transferResponse.status !== 202) {
      throw new Error(`Expected 202 Accepted, got ${transferResponse.status}`);
    }

    const jobInfo = await waitForTransferCompletion(
      transferResponse.data.job_id,
      sourceOutboundUrl,
    );

    if (!jobInfo.new_patient_id) {
      throw new Error('Transfer completed but missing new_patient_id');
    }

    const existsInTarget = await checkPatientExists(
      jobInfo.new_patient_id,
      targetFhirUrl,
    );
    if (!existsInTarget) {
      throw new Error(
        `Patient ${jobInfo.new_patient_id} not found in target FHIR`,
      );
    }

    logger.info(`Transfer to ${targetProvince} succeeded for ${patientId}`);

    logger.info(
      `Retrying transfer to ${targetProvince} for ${patientId} to confirm failure`,
    );

    await verifyTransferFailure(patientId, sourceOutboundUrl, targetProvince);
  } catch (error: unknown) {
    let errorMessage: string;

    if (isAxiosError(error)) {
      const status = error.response?.status ?? 'no status';
      const responseData = error.response?.data
        ? JSON.stringify(error.response.data)
        : 'no response';
      errorMessage = `Server responded with ${status} - ${responseData}`;
    } else {
      errorMessage =
        error instanceof Error ? error.message : 'Unknown error occurred';
    }

    throw Error(
      `Failure during transfer of ${patientId} to ${targetProvince}: ${errorMessage}`,
    );
  }
}

async function testRandomPatientTransfers() {
  try {
    logger.info('Starting province transfer tests');

    // Test BC -> ON
    await testProvinceTransfer(BC_OUTBOUND_URL, ON_FHIR_URL, 'ON');

    // Test ON -> BC
    await testProvinceTransfer(ON_OUTBOUND_URL, BC_FHIR_URL, 'BC');

    logger.info('All transfers validated successfully');
  } catch (error) {
    logger.error('Test failure:', {
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      responseData: isAxiosError(error) ? error.response?.data : undefined,
    });

    throw error;
  }
}

testRandomPatientTransfers().catch((error) => {
  logger.error('Test suite failed:', error);
  process.exit(1);
});
