import { describe, expect, it } from "vitest";
import {
  FORBIDDEN_METRIC_RESULT_KEYS,
  type MetricResult,
} from "../src/metrics/metricResult";
import { UnavailableInsightsApiClient } from "../src/api/insightsApi";
import { SYNTHETIC_MOCK_RESULTS } from "../src/api/syntheticMocks";
import { isUnavailableNotZero } from "../src/states/uiState";
import { V02_OVERVIEW_METRIC_IDS } from "../src/dashboard/labels";

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

  it("covers the nine v0.2.0 overview metrics", () => {
    const ids = new Set(SYNTHETIC_MOCK_RESULTS.map((r) => r.metric_id));
    for (const id of V02_OVERVIEW_METRIC_IDS) {
      expect(ids.has(id)).toBe(true);
    }
  });
});

describe("API boundary", () => {
  it("production-style client returns unavailable, not zero", async () => {
    const client = new UnavailableInsightsApiClient();
    const metric = await client.getMetric("total_assessments");
    expect(metric.completeness).toBe("unavailable");
    expect(metric.value).toBeNull();
    expect(isUnavailableNotZero("unavailable")).toBe(true);
  });

  it("zero-response sentiment is distinct from a zero score", () => {
    const sentiment = SYNTHETIC_MOCK_RESULTS.find(
      (r) => r.metric_id === "community_sentiment",
    );
    expect(sentiment?.value).toBeNull();
    expect(sentiment?.completeness).toBe("complete");
    expect(sentiment?.denominator).toBe(0);
    expect(sentiment?.limitations).toContain("no_responses_yet");
  });
});
