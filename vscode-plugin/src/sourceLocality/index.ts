/** Slice 13.10 source-locality public exports. */

export {
  SOURCE_LOCALITY_POLICY_ID,
  SOURCE_LOCALITY_POLICY_VERSION,
  DEFAULT_SOURCE_LOCALITY_LIMITATIONS,
  createSourceLocalityPolicy,
  sourceLocalityPolicyToStableDict,
  type SourceLocalityPolicy,
} from "./policy";

export {
  LOCALITY_RESULT_CATEGORIES,
  LOCALITY_OPERATIONS,
  GENERATED_ARTIFACT_CLASSES,
  APPROVED_ENGINE_ARTIFACT_BASENAMES,
  createSourceLocalityResult,
  sourceLocalityResultToStableDict,
  expectedCategoryForOperation,
  type LocalityResultCategory,
  type LocalityOperation,
  type GeneratedArtifactClass,
  type SourceLocalityResult,
} from "./results";

export {
  createSourceLocalityDiagnostics,
  sourceLocalityDiagnosticsToStableDict,
  localityDiagnosticsContainForbiddenKeys,
  type SourceLocalityDiagnostics,
} from "./diagnostics";

export {
  SOURCE_LOCALITY_CLAIMS,
  FORBIDDEN_OVERCLAIMS,
  claimsToStableDict,
} from "./claims";
