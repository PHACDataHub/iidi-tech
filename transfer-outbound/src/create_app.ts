import cors from 'cors';
import express from 'express';

import { get_env } from './env.ts';

import { expressErrorHandler } from './error_utils.ts';
import {
  assert_patient_exists_and_can_be_transferred,
  get_patient_bundle_for_transfer,
} from './fhir_utils.ts';
import {
  assert_patient_id_parameter_is_valid,
  assert_transfer_code_parameter_is_valid,
} from './request_parameter_validation_utils.ts';
import { query_param_to_int_or_undefined } from './request_utils.ts';
import {
  initialize_transfer_request,
  get_transfer_request_by_id,
  get_transfer_requests,
  get_transfer_request_job_info,
} from './transfer_request_queue/transfer_request_utils.ts';

export const create_app = async () => {
  const { TRANSFER_DASHBOARD_ORIGINS } = get_env();

  const app = express();

  // we'll need to be able to read `X-Forwarded-*` headers, both in prod and when using the dev docker setup
  app.set('trust proxy', true);

  // Only need CORS for PoC demo purposes, given the React SPA demo dashboard.
  // Wouldn't expect browsers to be directly hitting this API in reality
  app.use(cors({ origin: TRANSFER_DASHBOARD_ORIGINS }));

  app.use(express.json()); // parses JSON body payloads, converts req.body from a string to object
  app.use(express.urlencoded({ extended: false })); // parses URL-encoded payload parameters on POST/PUT in to req.body fields

  app.get('/healthcheck', (_req, res) => {
    // TODO consider if a non-trivial healthcheck is appropriate/useful.
    res.status(200).send();
  });

  app.get('/transfer-request', async (req, res) => {
    const { start, end } = req.query;

    const jobs = await get_transfer_requests(
      query_param_to_int_or_undefined(start),
      query_param_to_int_or_undefined(end),
    );

    const jobs_info = await Promise.all(
      jobs.map(get_transfer_request_job_info),
    );

    res.status(200).send(jobs_info);
  });

  app.post('/transfer-request', async (req, res) => {
    const { patient_id, transfer_to } = req.body;
    assert_patient_id_parameter_is_valid(patient_id);
    assert_transfer_code_parameter_is_valid(transfer_to);

    await assert_patient_exists_and_can_be_transferred(patient_id);

    const transfer_request_job = await initialize_transfer_request(
      patient_id,
      transfer_to,
    );

    const info = await get_transfer_request_job_info(transfer_request_job);

    res.status(202).type('json').send(info);
  });

  app.get('/transfer-request/dry-run', async (req, res) => {
    const { patient_id } = req.body;
    assert_patient_id_parameter_is_valid(patient_id);

    await assert_patient_exists_and_can_be_transferred(patient_id);

    const bundle = await get_patient_bundle_for_transfer(patient_id);

    res.status(200).type('json').send({ bundle });
  });

  app.get('/transfer-request/:transferRequestId', async (req, res) => {
    const transfer_request_job = await get_transfer_request_by_id(
      req.params.transferRequestId,
    );

    if (transfer_request_job === undefined) {
      res.status(404).send();
    } else {
      const info = await get_transfer_request_job_info(transfer_request_job);
      res.status(200).type('json').send(info);
    }
  });

  app.get('/patient/:patientId/transfer-request', async (req, res) => {
    const { patientId: patient_id } = req.params;
    assert_patient_id_parameter_is_valid(patient_id);

    const { start, end } = req.query;
    const start_number = query_param_to_int_or_undefined(start);
    const end_number = query_param_to_int_or_undefined(end);

    const all_jobs = await get_transfer_requests(start_number, end_number);

    const paginated_filtered_jobs = all_jobs.filter(
      (job) => job.data.patient_id === patient_id,
    );

    const jobs_info = await Promise.all(
      paginated_filtered_jobs.map(get_transfer_request_job_info),
    );
    res.status(200).type('json').send(jobs_info);
  });

  app.use(expressErrorHandler);

  return app;
};
