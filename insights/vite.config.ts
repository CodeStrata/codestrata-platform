import { execSync } from "node:child_process";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

function resolveBuildId(): string {
  try {
    const short = execSync("git rev-parse --short HEAD", { encoding: "utf8" }).trim();
    // Suffix marks the Chrome unbound-fetch Illegal invocation fix.
    return `sv17-24-${short}-b3`;
  } catch {
    return `sv17-24-${Date.now().toString(36)}-b3`;
  }
}

const insightsBuildId = resolveBuildId();

export default defineConfig({
  plugins: [
    react(),
    {
      name: "insights-build-id",
      transformIndexHtml(html) {
        return html.replace(
          "</head>",
          `    <meta name="codestrata-insights-build" content="${insightsBuildId}" />\n  </head>`,
        );
      },
    },
  ],
  define: {
    __INSIGHTS_BUILD_ID__: JSON.stringify(insightsBuildId),
  },
  build: {
    sourcemap: false,
    reportCompressedSize: false,
  },
  server: {
    port: 5180,
  },
});
