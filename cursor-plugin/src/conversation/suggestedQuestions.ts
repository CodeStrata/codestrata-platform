/** Suggested repository-aware prompts grounded in Engineering Intelligence. */

export type PromptCategory =
  | "Understand"
  | "Prioritize"
  | "Plan"
  | "Explain"
  | "Validate";

export interface SuggestedQuestion {
  id: string;
  title: string;
  purpose: string;
  prompt: string;
  category: PromptCategory;
  requiresAssessment: boolean;
  scope: string;
}

export const SUGGESTED_QUESTIONS: SuggestedQuestion[] = [
  {
    id: "highest-priority",
    title: "Highest-priority findings",
    purpose: "Identify top risks from the assessment",
    category: "Prioritize",
    requiresAssessment: true,
    scope: "general",
    prompt:
      "Using only the CodeStrata Engineering Assessment findings and recommendations in context, what are the highest-priority engineering risks in this repository? Cite finding titles/rule IDs. Do not invent findings.",
  },
  {
    id: "architecture-risks",
    title: "Summarize architecture risks",
    purpose: "Architecture-focused assessment summary",
    category: "Understand",
    requiresAssessment: true,
    scope: "architecture",
    prompt:
      "Summarize the architecture risks from the CodeStrata Engineering Assessment. Use only findings/recommendations in context; say if architecture evidence is missing.",
  },
  {
    id: "tech-debt-first",
    title: "Technical debt to address first",
    purpose: "Prioritize debt work from recommendations",
    category: "Prioritize",
    requiresAssessment: true,
    scope: "technical-debt",
    prompt:
      "Which technical debt should be addressed first according to the CodeStrata assessment? Cite priorities and related findings only from context.",
  },
  {
    id: "explain-ar-001",
    title: "Explain rule AR-001",
    purpose: "Explain a specific rule if present",
    category: "Explain",
    requiresAssessment: true,
    scope: "architecture",
    prompt:
      "Explain Rule AR-001 using any matching CodeStrata findings/recommendations. If the assessment has no AR-001 items, say so clearly — do not invent the rule outcome.",
  },
  {
    id: "dependencies",
    title: "Dependencies needing attention",
    purpose: "Dependency findings from assessment",
    category: "Understand",
    requiresAssessment: true,
    scope: "dependencies",
    prompt:
      "From the CodeStrata Engineering Assessment, which dependencies require attention? Use assessment evidence only.",
  },
  {
    id: "first-sprint",
    title: "First modernization sprint",
    purpose: "Plan from recommendations",
    category: "Plan",
    requiresAssessment: true,
    scope: "modernization",
    prompt:
      "What should be included in the first modernization sprint based on CodeStrata recommendations and findings? Distinguish assessment evidence from your planning inference.",
  },
  {
    id: "evidence-vs-inferred",
    title: "Evidence-backed vs inferred",
    purpose: "Validate grounding quality",
    category: "Validate",
    requiresAssessment: true,
    scope: "general",
    prompt:
      "Which important claims about this repository are evidence-backed by CodeStrata findings versus inferred? List both clearly; do not invent findings.",
  },
  {
    id: "missing-info",
    title: "What is missing from this assessment?",
    purpose: "Surface assessment gaps",
    category: "Validate",
    requiresAssessment: true,
    scope: "general",
    prompt:
      "What information is missing from this CodeStrata Engineering Assessment for confident modernization decisions? Absence of a finding is not proof an issue does not exist.",
  },
  {
    id: "files-first",
    title: "Which files to inspect first?",
    purpose: "Evidence paths from findings",
    category: "Plan",
    requiresAssessment: true,
    scope: "general",
    prompt:
      "Which files should I inspect first based on CodeStrata finding evidence paths? Prefer highest-severity findings. Inspect code before proposing exact edits.",
  },
  {
    id: "implementation-plan",
    title: "Implementation plan from recommendations",
    purpose: "Turn recommendations into a plan",
    category: "Plan",
    requiresAssessment: true,
    scope: "recommendations",
    prompt:
      "Create an implementation plan based on the CodeStrata recommendations. Cite recommendation titles/priorities. Do not claim fixes are applied unless files were modified.",
  },
  {
    id: "group-severity",
    title: "Group findings by severity",
    purpose: "Severity overview",
    category: "Understand",
    requiresAssessment: true,
    scope: "general",
    prompt:
      "Group the CodeStrata Engineering Assessment findings by severity and summarize each group using only context.",
  },
  {
    id: "cloud-readiness",
    title: "Cloud readiness findings",
    purpose: "Cloud-related assessment items",
    category: "Explain",
    requiresAssessment: true,
    scope: "cloud",
    prompt:
      "Which CodeStrata findings affect cloud readiness? Filter from assessment context only.",
  },
];

export function questionsByCategory(): Map<PromptCategory, SuggestedQuestion[]> {
  const map = new Map<PromptCategory, SuggestedQuestion[]>();
  for (const question of SUGGESTED_QUESTIONS) {
    const list = map.get(question.category) ?? [];
    list.push(question);
    map.set(question.category, list);
  }
  return map;
}
