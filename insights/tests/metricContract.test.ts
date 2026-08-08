import { describe, expect, it } from "vitest";
import {
  FORBIDDEN_METRIC_RESULT_KEYS,
  SUPPRESSED_GROUP_KEY,
  type MetricResult,
} from "../src/metrics/metricResult";
import { UnavailableInsightsApiClient } from "../src/api/insightsApi";
import { SYNTHETIC_MOCK_RESULTS } from "../src/api/syntheticMocks";
import { isUnavailableNotZero } from "../src/states/uiState";

describe("MetricResult contract", () => {
  it("matches required fields", () => {
    const sample: MetricResult = SYNTHETIC_MOCK_RESULTS[0];
    expect(sample).toHaveProperty("metric_id");
    expect(sample).toHaveProperty("status");
    expect(sample).toHaveProperty("window");
    expect(sample).toHaveProperty("value");
    expect(sample).toHaveProperty("groups");
    expect(sample).toHaveProperty("completeness");
    expect(sample).toHaveProperty("denominator");
    expect(sample).toHaveProperty("share");
    expect(sample).toHaveProperty("limitations");
  });

  it("forbids privacy-sensitive keys in result objects", () => {
    const serialized = JSON.stringify(SYNTHETIC_MOCK_RESULTS);
    for (const key of FORBIDDEN_METRIC_RESULT_KEYS) {
      expect(serialized.includes(`"${key}"`)).toBe(false);
    }
  });

  it("uses other_suppressed without leaking hidden categories", () => {
    const cli = SYNTHETIC_MOCK_RESULTS.find((r) => r.metric_id === "cli_version_adoption");
    expect(cli).toBeDefined();
    const groups = cli!.groups;
    expect(groups.some((g) => g.key === SUPPRESSED_GROUP_KEY && g.suppressed)).toBe(
      true,
    );
    expect(groups.every((g) => g.key !== "installation_id")).toBe(true);
  });
});

describe("API boundary", () => {
  it("production-style client returns unavailable, not zero", async () => {
    const client = new UnavailableInsightsApiClient();
    const metric = await client.getMetric("total_anonymous_installations");
    expect(metric.completeness).toBe("unavailable");
    expect(metric.value).toBeNull();
    expect(isUnavailableNotZero("unavailable")).toBe(true);
  });

  it("zero is distinct from unavailable", () => {
    const zero = SYNTHETIC_MOCK_RESULTS[0];
    expect(zero.value).toBe(0);
    expect(zero.completeness).toBe("complete");
  });
});
