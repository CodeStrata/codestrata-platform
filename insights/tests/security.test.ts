import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("security and privacy static checks", () => {
  const srcRoot = resolve(here, "../src");

  it("does not import AWS SDK or S3 clients", () => {
    const files = [
      "main.tsx",
      "app/App.tsx",
      "api/insightsApi.ts",
      "pages/DashboardPage.tsx",
    ];
    for (const rel of files) {
      const text = readFileSync(resolve(srcRoot, rel), "utf8");
      expect(text).not.toMatch(/aws-sdk|@aws-sdk|boto3|S3Client|SecretsManager/i);
      expect(text).not.toMatch(/dangerouslySetInnerHTML|localStorage\.setItem\(['\"]token/);
    }
  });

  it("index.html sets noindex robots and security headers", () => {
    const html = readFileSync(resolve(here, "../index.html"), "utf8");
    expect(html).toContain('name="robots" content="noindex,nofollow"');
    expect(html).toContain('lang="en"');
    expect(html).toContain("Content-Security-Policy");
    expect(html).toContain("X-Content-Type-Options");
    expect(html).toContain("frame-ancestors 'none'");
  });

  it("does not hardcode dashboard password", () => {
    const login = readFileSync(resolve(srcRoot, "pages/LoginPage.tsx"), "utf8");
    expect(login).not.toMatch(/password\s*===\s*['\"]/);
    expect(login).not.toMatch(/localStorage|sessionStorage/);
  });
});
