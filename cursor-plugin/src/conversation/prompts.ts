/**
 * Prompt construction: Assessment → Findings → Recommendations → User Question.
 * Never injects raw repository source code.
 */

import type { ConversationContext } from "./context";

export interface ConstructedPrompt {
  systemPreamble: string;
  assessmentBlock: string;
  userQuestion: string;
  fullPrompt: string;
  hasAssessment: boolean;
}

const SYSTEM_PREAMBLE =
  "You are assisting with a CodeStrata Engineering Assessment (Community Edition). " +
  "Use only the provided Engineering Intelligence artifacts (findings and recommendations). " +
  "Do not invent findings. Distinguish fact, assessment conclusion, and inference. " +
  "Do not claim Platform, Portfolio, or Executive Intelligence capabilities. " +
  "Inspect repository code before suggesting exact edits. Preserve developer control.";

export function constructPrompt(
  context: ConversationContext,
  userQuestion: string
): ConstructedPrompt {
  const question = userQuestion.trim() || "Summarize the Engineering Assessment.";
  const assessmentBlock = context.markdown;
  const fullPrompt = [
    SYSTEM_PREAMBLE,
    "",
    "---",
    "",
    assessmentBlock,
    "",
    "---",
    "",
    "## Developer question",
    "",
    question,
    "",
  ].join("\n");

  return {
    systemPreamble: SYSTEM_PREAMBLE,
    assessmentBlock,
    userQuestion: question,
    fullPrompt,
    hasAssessment: true,
  };
}

export function constructPromptWithoutAssessment(userQuestion: string): ConstructedPrompt {
  const question = userQuestion.trim();
  const fullPrompt = [
    SYSTEM_PREAMBLE,
    "",
    "No valid CodeStrata Engineering Assessment context is loaded.",
    "Do not invent findings, severities, or recommendations.",
    "Tell the developer to run CodeStrata: Engineering Assessment first.",
    "",
    "## Developer question",
    "",
    question || "(empty)",
    "",
  ].join("\n");
  return {
    systemPreamble: SYSTEM_PREAMBLE,
    assessmentBlock: "",
    userQuestion: question,
    fullPrompt,
    hasAssessment: false,
  };
}
