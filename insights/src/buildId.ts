/** Harmless public build identifier for owner/Chrome deployment checks. */

declare const __INSIGHTS_BUILD_ID__: string | undefined;

export const INSIGHTS_BUILD_ID: string =
  typeof __INSIGHTS_BUILD_ID__ === "string" && __INSIGHTS_BUILD_ID__.length > 0
    ? __INSIGHTS_BUILD_ID__
    : "sv17-24-dev";
