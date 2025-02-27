import type { Request, Response, NextFunction } from 'express';

import { get_env } from './env.ts';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SerializableErrorData = Record<string, any>;

export class AppError extends Error {
  status: number;
  errorData?: SerializableErrorData;

  constructor(
    status: number,
    message: string,
    errorData?: SerializableErrorData,
  ) {
    super(message);
    this.status = status;
    this.errorData = errorData;
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
    details?: SerializableErrorData;
  } = {
    error: err.message,
  };

  if (err instanceof AppError && err.errorData) {
    try {
      JSON.parse(JSON.stringify(err.errorData));
      errorResponse.details = err.errorData;
    } catch (e) {
      console.error('Invalid error data provided:', e);
    }
  }

  res.status(get_status_code(err)).json(errorResponse);
};
