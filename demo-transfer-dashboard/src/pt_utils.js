export const pt_codes = ['BC', 'ON'];

export const pt_name_by_code = {
  BC: 'British Columbia',
  ON: 'Ontario',
};

export const transfer_service_url_by_pt_code = {
  BC: process.env.BC_OUTBOUND_URL,
  ON: process.env.ON_OUTBOUND_URL,
};

export const get_default_pt = () => {
  const default_pt_query_param = new URLSearchParams(
    window.location.search,
  ).get('default_pt');

  return pt_codes.includes(default_pt_query_param)
    ? default_pt_query_param
    : pt_codes[0];
};
