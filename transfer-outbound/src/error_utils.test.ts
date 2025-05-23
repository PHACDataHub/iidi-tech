import express from 'express';
import request from 'supertest';

import { AppError, expressErrorHandler } from './error_utils.ts';

describe('AppError', () => {
  it('constructs a new error with the provided message and the additional status property', () => {
    const message = 'test message for testing the message';
    const status = 123;

    const appError = new AppError(status, message);

    expect(appError).toBeInstanceOf(Error);
    expect(appError).toBeInstanceOf(AppError);
    expect(appError.status).toBe(status);
    expect(appError.message).toContain(message);
    expect(appError.message).toContain(status.toString());
  });
});

describe('expressErrorHandler middleware', () => {
  it('handles errors passed to next() by express routes', async () => {
    const app = express();

    const status_code = 500;

    app.get('/error-via-next', function (_req, _res, next) {
      next(new AppError(status_code, 'error'));
    });

    const mockedErrorHandler = jest.fn(expressErrorHandler);
    app.use(mockedErrorHandler);

    const response = await request(app)
      .get('/error-via-next')
      .set('Accept', 'application/json');

    expect(mockedErrorHandler).toHaveBeenCalledTimes(1);
    expect(response.status).toBe(status_code);
  });

  it('handles errors thrown by express routes', async () => {
    const app = express();

    const status_code = 500;

    app.get('/error-via-next', function (_req, _res, _next) {
      throw new AppError(status_code, 'error');
    });

    const mockedErrorHandler = jest.fn(expressErrorHandler);
    app.use(mockedErrorHandler);

    const response = await request(app)
      .get('/error-via-next')
      .set('Accept', 'application/json');

    expect(mockedErrorHandler).toHaveBeenCalled();
    expect(response.status).toBe(status_code);
  });

  it('sets the response status based on the error, includes the error message in the response body', async () => {
    const app = express();

    const status_code = 418;
    const error_message = "I'm a teapot";

    app.get('/error', function (_req, _res, _next) {
      throw new AppError(status_code, error_message);
    });

    const mockedErrorHandler = jest.fn(expressErrorHandler);
    app.use(mockedErrorHandler);

    const response = await request(app)
      .get('/error')
      .set('Accept', 'application/json');

    expect(mockedErrorHandler).toHaveBeenCalled();
    expect(response.status).toBe(status_code);
    expect(response.body.error).toBe(error_message);
  });

  it('includes additional error data in the response when present', async () => {
    const app = express();
    const status_code = 400;
    const errorDetails = {
      location: 'body',
      diagnostics: 'Invalid data',
      details: 'Details about the error',
    };

    app.get('/error', function (_req, _res, _next) {
      throw new AppError(status_code, 'Validation failed', errorDetails);
    });

    const mockedErrorHandler = jest.fn(expressErrorHandler);
    app.use(mockedErrorHandler);

    const response = await request(app)
      .get('/error')
      .set('Accept', 'application/json');

    expect(mockedErrorHandler).toHaveBeenCalled();
    expect(response.status).toBe(status_code);
    expect(response.body.error).toBe('Validation failed');
    expect(response.body.details).toEqual(errorDetails);
  });

  it('handles non-serializable error data gracefully', async () => {
    const app = express();
    const status_code = 400;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const errorDetails: { circular: { self?: any } } = {
      circular: {},
    };
    // Creating a circular reference to trigger error in parsing to JSON
    errorDetails.circular.self = errorDetails;

    app.get('/error', function (_req, _res, _next) {
      throw new AppError(status_code, 'Bad data', errorDetails);
    });

    const mockedErrorHandler = jest.fn(expressErrorHandler);
    app.use(mockedErrorHandler);

    const response = await request(app)
      .get('/error')
      .set('Accept', 'application/json');

    expect(mockedErrorHandler).toHaveBeenCalled();
    expect(response.status).toBe(status_code);
    expect(response.body.error).toBe('Bad data');
    expect(response.body.details).toBeUndefined();
  });
});
