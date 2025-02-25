import type { Request, Response, NextFunction } from 'express';

import { get_env } from './env.ts';

interface FHIRValidationError {
  location: string;
  diagnostics: string;
  details: string;
}

export class AppError extends Error {
  status: number;
  FHIRValidationError?: FHIRValidationError[];

  constructor(
    status: number,
    message: string,
    FHIRValidationError?: FHIRValidationError[],
  ) {
    super(message);
    this.status = status;
    this.FHIRValidationError = FHIRValidationError;
  }
}

const handle_error_logging = (err: Error | AppError) => {
  const { DEV_IS_TEST_ENV } = get_env();

  if (!DEV_IS_TEST_ENV) {
    // TODO: a good structured logging library and logging utils are a TODO
    // console output should be silenced when running tests, for clean test reports
    console.error(err.stack);
  }
};

const get_status_code = (err: Error | AppError) =>
  'status' in err ? err.status : 500;

export const expressErrorHandler = (
  err: Error | AppError,
  _req: Request,
  res: Response,
  _next: NextFunction,
) => {
  handle_error_logging(err);

  const errorResponse: {
    error: string;
    validationError?: FHIRValidationError[];
  } = {
    error: err.message,
  };

  if (err instanceof AppError && err.FHIRValidationError) {
    errorResponse.validationError = err.FHIRValidationError;
  }

  res.status(get_status_code(err)).json(errorResponse);
};
