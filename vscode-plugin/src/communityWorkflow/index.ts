/** Community VS Code workflow contract (Slice 13.1). */

export {
  WORKFLOW_POLICY_ID,
  WORKFLOW_POLICY_VERSION,
  DEFAULT_WORKFLOW_LIMITATIONS,
  createWorkflowPolicy,
  workflowPolicyToStableDict,
  type CommunityWorkflowPolicy,
} from "./policy";

export { WORKFLOW_STATES, isWorkflowState, type WorkflowState } from "./states";

export {
  WORKFLOW_OPERATIONS,
  WORKFLOW_COMMAND_IDS,
  COMMAND_TO_OPERATION,
  COMPATIBILITY_ALIASES,
  operationForCommand,
  isWorkflowOperation,
  type WorkflowOperation,
  type WorkflowCommandId,
} from "./operations";

export {
  createWorkflowContext,
  workflowContextToStableDict,
  type WorkflowContext,
  type WorkspaceKind,
  type TelemetryDecisionCategory,
} from "./context";

export {
  WORKFLOW_RESULT_STATUSES,
  communityWorkflowResultToStableDict,
  type CommunityWorkflowResult,
  type WorkflowResultStatus,
  type PrimaryExitCategory,
} from "./results";

export {
  WORKFLOW_ERROR_CATEGORIES,
  WorkflowTransitionError,
  type WorkflowErrorCategory,
} from "./errors";

export { ALLOWED_TRANSITIONS, canTransition, assertTransition } from "./transitions";

export {
  workflowDiagnosticsToStableDict,
  diagnosticsContainForbiddenKeys,
  type WorkflowDiagnostics,
} from "./diagnostics";

export {
  classifyWorkspaceKind,
  workspaceIsEligible,
  type WorkspaceEligibilityInput,
} from "./workspace";

export {
  CommunityWorkflowSession,
  mapConsentToDecisionCategory,
  type WorkflowSessionOptions,
} from "./orchestration";
