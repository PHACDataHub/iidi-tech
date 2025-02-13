import type { Request } from 'express';
import _ from 'lodash';

export const query_param_to_int_or_undefined = (
  query_param: Request['query'][string],
) =>
  query_param === undefined
    ? undefined
    : _.isInteger(+query_param)
      ? +query_param
      : undefined;
