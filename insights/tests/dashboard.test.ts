import { describe, expect, it } from "vitest";
import { formatCount, formatShare, groupLabel } from "../src/dashboard/format";
import {
  humanizeLimitations,
  METRIC_DISPLAY_NAMES,
  V02_OVERVIEW_METRIC_IDS,
} from "../src/dashboard/labels";
import {
  assertSyntheticCoversV02Overview,
  SYNTHETIC_MOCK_RESULTS,
} from "../src/api/syntheticMocks";

describe("dashboard presentation helpers", () => {
  it("formats counts and shares without recomputation", () => {
    expect(formatCount(0)).toBe("0");
    expect(formatCount(1234)).toBe("1,234");
    expect(formatShare(0.625)).toBe("63%");
    expect(formatShare(null)).toBeNull();
  });

  it("labels suppressed groups without leaking categories", () => {
    expect(groupLabel("other_suppressed", true)).toBe("Other (suppressed)");
    expect(groupLabel("0.2.0", false)).toBe("0.2.0");
  });

  it("maps known limitations only", () => {
    expect(humanizeLimitations(["suppressed_small_groups", "weird_unknown"])).toEqual([
      "Small groups are suppressed for privacy.",
    ]);
  });

  it("exposes exactly nine v0.2.0 overview metrics", () => {
    expect(V02_OVERVIEW_METRIC_IDS).toHaveLength(9);
    expect(METRIC_DISPLAY_NAMES.total_assessments).toBe("Total Assessments");
    expect(METRIC_DISPLAY_NAMES.github_stars).toBe("GitHub Stars");
    expect(METRIC_DISPLAY_NAMES.community_sentiment).toBe("Community Sentiment");
  });

  it("synthetic fixtures stay aggregate-only and cover the nine metrics", () => {
    assertSyntheticCoversV02Overview();
    const blob = JSON.stringify(SYNTHETIC_MOCK_RESULTS);
    for (const bad of [
      "installation_id",
      "event_id",
      "s3_key",
      "model_id",
      "repository_name",
      "prompt",
    ]) {
      expect(blob).not.toContain(bad);
    }
  });
});
