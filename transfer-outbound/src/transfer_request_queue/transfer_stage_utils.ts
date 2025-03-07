export const initial_stage = 'collecting_and_transfering';

export const terminal_stage = 'done';

export const transfer_stages = [
  initial_stage,
  'setting_patient_post_transfer_metadata',
  terminal_stage,
] as const;
export type transferStage = (typeof transfer_stages)[number];

const non_terminal_transfer_stages = transfer_stages.filter(
  (stage) => stage !== terminal_stage,
);
type nonTerminalTransferStage = (typeof non_terminal_transfer_stages)[number];

const next_stage_map: Record<nonTerminalTransferStage, transferStage> = {
  collecting_and_transfering: 'setting_patient_post_transfer_metadata',
  setting_patient_post_transfer_metadata: terminal_stage,
};
export const get_next_stage = (
  current_stage: Exclude<transferStage, typeof terminal_stage>,
): transferStage => {
  if (!non_terminal_transfer_stages.includes(current_stage)) {
    throw new Error(
      `Unexpected transfer stage "${current_stage}". Should be in [${non_terminal_transfer_stages.join(', ')}]`,
    );
  }

  if (current_stage in next_stage_map) {
    return next_stage_map[current_stage];
  } else {
    throw new Error(
      `Stage "${current_stage}" is a valid non-terminal stage, but does not have a next stage? Implementation error!`,
    );
  }
};
