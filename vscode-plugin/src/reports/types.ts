/** Report JSON types — subset of public report.json / findings.json contracts. */

export interface EvidenceRef {
  path?: string | null;
  excerpt?: string | null;
  evidence_type?: string | null;
  source_id?: string | null;
}

export interface Finding {
  id: string;
  title: string;
  description?: string;
  severity: string;
  category?: string;
  rule_id?: string;
  evidence?: EvidenceRef[];
}

export interface Recommendation {
  id: string;
  title: string;
  description?: string;
  rationale?: string;
  priority?: string;
  category?: string;
  rule_id?: string;
  related_finding_ids?: string[];
  effort?: string;
  risk?: string;
  actions?: string[];
}

export interface ReportManifest {
  schema_version?: string;
  product_name?: string;
  edition?: string;
  report_type?: string;
  brand_report_name?: string;
  generation_mode?: string;
}

export interface ParsedAssessmentArtifacts {
  runDirectory: string;
  htmlReportPath?: string;
  jsonReportPath?: string;
  findingsPath?: string;
  findings: Finding[];
  recommendations: Recommendation[];
  manifest?: ReportManifest;
  schemaError?: string;
  parseWarnings: string[];
}
