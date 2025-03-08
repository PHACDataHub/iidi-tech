export const initial_stage = 'collecting_and_transfering';

export const terminal_stages = ['done', 'rejected'] as const;
export type terminalStage = (typeof terminal_stages)[number];

const non_terminal_transfer_stages = [
  initial_stage,
  'setting_patient_post_transfer_metadata',
] as const;
type nonTerminalTransferStage = (typeof non_terminal_transfer_stages)[number];

export const transfer_stages = [
  ...non_terminal_transfer_stages,
  ...terminal_stages,
];
export type transferStage = (typeof transfer_stages)[number];

export const is_non_terminal_stage = (
  stage: unknown,
): stage is nonTerminalTransferStage =>
  non_terminal_transfer_stages.includes(stage as nonTerminalTransferStage);

const next_stage_map: Record<nonTerminalTransferStage, transferStage> = {
  collecting_and_transfering: 'setting_patient_post_transfer_metadata',
  setting_patient_post_transfer_metadata: 'done',
};
export const get_next_stage = (
  current_stage: nonTerminalTransferStage,
): transferStage => {
  if (!is_non_terminal_stage(current_stage)) {
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
