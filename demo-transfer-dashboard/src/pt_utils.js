export const pt_codes = ['BC', 'ON'];

export const pt_name_by_code = {
  BC: 'British Columbia',
  ON: 'Ontario',
};

export const transfer_service_url_by_pt_code = {
  BC: process.env.BC_OUTBOUND_URL,
  ON: process.env.ON_OUTBOUND_URL,
};

export const get_outbound_pt = () => {
  const outbound_pt_query_param = new URLSearchParams(
    window.location.search,
  ).get('pt');

  return pt_codes.includes(outbound_pt_query_param)
    ? outbound_pt_query_param
    : pt_codes[0];
};
