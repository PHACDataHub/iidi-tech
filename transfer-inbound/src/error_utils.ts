import type { Request, Response, NextFunction } from 'express';

import { get_env } from './env.ts';

// TODO deduplicate against transfer-outbound error_utils.ts

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SerializableErrorData = Record<string, any>;

const get_app_error_data = (errorData?: SerializableErrorData) => {
  if (errorData !== undefined) {
    try {
      JSON.parse(JSON.stringify(errorData));
      return errorData;
    } catch {
      console.error(
        `Invalid error data provided, not JSON serializable. Received: "${errorData}"`,
      );
    }
  }
};
const get_app_error_message = (
  status: number,
  message: string,
  errorData?: SerializableErrorData,
) => {
  return `Status: "${status}". Message: "${message}". ${get_app_error_data(errorData) !== undefined ? `Error data: ${JSON.stringify(get_app_error_data(errorData))}.` : ''}`;
};
export class AppError extends Error {
  message_raw: string;
  status: number;
  errorData?: SerializableErrorData;

  constructor(
    status: number,
    message: string,
    errorData?: SerializableErrorData,
  ) {
    super(get_app_error_message(status, message, errorData));
    this.message_raw = message;
    this.status = status;
    this.errorData = get_app_error_data(errorData);
  }

  toJSON() {
    return {
      error: this.message_raw,
      details: this.errorData,
    };
  }
}

const is_app_error = (err: Error | AppError): err is AppError =>
  'status' in err;

const handle_error_logging = (err: Error | AppError) => {
  const { DEV_IS_TEST_ENV } = get_env();

  if (!DEV_IS_TEST_ENV) {
    // TODO: a good structured logging library and logging utils are a TODO
    // console output should be silenced when running tests, for clean test reports
    console.error(err.stack);
  }
};

const get_status_code = (err: Error | AppError) =>
  is_app_error(err) ? err.status : 500;

export const expressErrorHandler = (
  err: Error | AppError,
  _req: Request,
  res: Response,
  _next: NextFunction,
) => {
  handle_error_logging(err);

  res
    .status(get_status_code(err))
    .json(is_app_error(err) ? err.toJSON() : { error: err.message });
};
