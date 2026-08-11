import { defineConfig } from "vitepress";

/**
 * CodeStrata Community Edition documentation (Slice 14.2).
 * Canonical public URL: https://docs.codestrata.ai
 *
 * Community-only active navigation. Design System: design-system/ (Slice 14.1).
 */
export default defineConfig({
  title: "CodeStrata Docs",
  description:
    "Community Edition documentation for CodeStrata Engine — install, assess, reports, VS Code, and privacy.",
  lang: "en-US",
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: false,
  /** Light-first (Design System default); dark available via toggle. */
  appearance: true,
  srcExclude: [
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "PRIVACY.md",
    "SUPPORT.md",
    "CONTRIBUTING.md",
    "VISUAL_REGRESSION.md",
    "ARCHITECTURE.md",
    "CI.md",
    "DEPLOYMENT.md",
    "EXTRACTION.md",
    "MIGRATION_PLAN.md",
    "WEBSITE_STYLE_ALIGNMENT.md",
    "platform/**",
    "community/vs-platform.md",
    "internal/**",
    "**/node_modules/**",
  ],
  head: [
    ["link", { rel: "icon", href: "/favicon.ico", sizes: "any" }],
    ["link", { rel: "icon", href: "/favicon.png", type: "image/png", sizes: "32x32" }],
    ["link", { rel: "apple-touch-icon", href: "/apple-touch-icon.png", sizes: "180x180" }],
    [
      "link",
      {
        rel: "preload",
        href: "/fonts/inter-400-700-latin.woff2",
        as: "font",
        type: "font/woff2",
        crossorigin: "",
      },
    ],
    ["link", { rel: "stylesheet", href: "/fonts.css" }],
    ["meta", { name: "theme-color", content: "#f4f6f3" }],
    ["meta", { property: "og:type", content: "website" }],
    ["meta", { property: "og:title", content: "CodeStrata Community Docs" }],
    [
      "meta",
      {
        property: "og:description",
        content:
          "Community Edition documentation — Engine, assessments, reports, and VS Code.",
      },
    ],
    ["meta", { property: "og:url", content: "https://docs.codestrata.ai/" }],
    ["meta", { name: "twitter:card", content: "summary" }],
  ],
  markdown: {
    theme: {
      light: "github-dark",
      dark: "github-dark",
    },
  },
  themeConfig: {
    logo: {
      light: "/brand/lockup-horizontal-on-light.svg",
      dark: "/brand/lockup-horizontal-on-dark.svg",
      alt: "CodeStrata Docs",
    },
    // Docs brand → docs home. Company site is the explicit "Main Site" nav item.
    logoLink: "/",
    siteTitle: false,
    nav: [
      { text: "Get Started", link: "/getting-started/" },
      { text: "CLI", link: "/reference/cli" },
      { text: "VS Code", link: "/extensions/vscode" },
      { text: "Assessments", link: "/assessments/" },
      { text: "Reports", link: "/reports/" },
      {
        text: "Reference",
        items: [
          { text: "Configuration", link: "/reference/configuration" },
          { text: "AI Providers", link: "/ai-providers/" },
          { text: "Community API", link: "/reference/api" },
          { text: "Community Cloud API", link: "/reference/community-api/" },
          { text: "Architecture", link: "/architecture/" },
          { text: "Community Cloud", link: "/architecture/community-cloud" },
          { text: "Data Lake", link: "/architecture/data-lake" },
          { text: "Insights", link: "/architecture/insights" },
          { text: "Telemetry", link: "/reference/telemetry" },
          { text: "Data Collection", link: "/security/data-collection" },
          { text: "Collected Fields", link: "/security/collected-fields" },
          { text: "Privacy", link: "/security/privacy" },
          { text: "Source Locality", link: "/security/source-locality" },
          { text: "Retention & Deletion", link: "/security/retention-and-deletion" },
          { text: "Release Notes", link: "/reference/release-notes" },
        ],
      },
      { text: "FAQ", link: "/faq/" },
      {
        text: "Main Site",
        link: "https://codestrata.ai/",
      },
    ],
    sidebar: {
      "/": [
        {
          text: "Getting Started",
          items: [
            { text: "Overview", link: "/getting-started/" },
            { text: "Prerequisites", link: "/getting-started/prerequisites" },
            { text: "Installation", link: "/getting-started/install" },
            {
              text: "Repository Initialization",
              link: "/getting-started/repository-initialization",
            },
            {
              text: "First Assessment",
              link: "/getting-started/first-assessment",
            },
            { text: "Next Steps", link: "/getting-started/next-steps" },
          ],
        },
        {
          text: "Engine & CLI",
          items: [
            { text: "Engine Overview", link: "/engine/" },
            { text: "Installation", link: "/engine/installation" },
            { text: "Doctor", link: "/engine/doctor" },
            { text: "CLI Reference", link: "/reference/cli" },
            { text: "Configuration", link: "/reference/configuration" },
          ],
        },
        {
          text: "Assessments & Reports",
          items: [
            { text: "Running Assessments", link: "/assessments/" },
            {
              text: "Deterministic vs AI",
              link: "/assessments/deterministic-vs-ai",
            },
            { text: "Assessment Reports", link: "/reports/" },
            {
              text: "Findings & Recommendations",
              link: "/reports/findings",
            },
            {
              text: "Engineering Intelligence Reports",
              link: "/reports/engineering-intelligence",
            },
            { text: "JSON Reports", link: "/reference/json-reports" },
            { text: "Findings Reference", link: "/reference/findings" },
          ],
        },
        {
          text: "VS Code Extension",
          items: [
            { text: "Overview", link: "/extensions/" },
            { text: "VS Code", link: "/extensions/vscode" },
          ],
        },
        {
          text: "AI, Privacy & API",
          items: [
            { text: "AI Providers", link: "/ai-providers/" },
            { text: "Community API", link: "/reference/api" },
            { text: "Community Cloud API", link: "/reference/community-api/" },
            { text: "Architecture", link: "/architecture/" },
            { text: "Community Cloud", link: "/architecture/community-cloud" },
            { text: "Data Lake", link: "/architecture/data-lake" },
            { text: "Insights", link: "/architecture/insights" },
            { text: "Telemetry", link: "/reference/telemetry" },
            { text: "Data Collection", link: "/security/data-collection" },
            { text: "Collected Fields", link: "/security/collected-fields" },
            { text: "Privacy", link: "/security/privacy" },
            { text: "Source Locality", link: "/security/source-locality" },
            { text: "Retention & Deletion", link: "/security/retention-and-deletion" },
            { text: "Security", link: "/security/" },
            { text: "MCP", link: "/reference/mcp" },
            { text: "Compatibility", link: "/reference/compatibility" },
          ],
        },
        {
          text: "Help",
          items: [
            { text: "Troubleshooting", link: "/troubleshooting/" },
            { text: "FAQ", link: "/faq/" },
            { text: "Release Notes", link: "/reference/release-notes" },
            { text: "Examples", link: "/community/examples" },
            { text: "Contributing", link: "/community/contributing" },
          ],
        },
        {
          text: "Trust & Community",
          items: [
            { text: "Privacy", link: "/security/privacy" },
            { text: "Source Locality", link: "/security/source-locality" },
            { text: "Data Collection", link: "/security/data-collection" },
            { text: "Retention & Deletion", link: "/security/retention-and-deletion" },
            { text: "Telemetry", link: "/reference/telemetry" },
            { text: "AI Providers", link: "/ai-providers/" },
            { text: "Architecture", link: "/architecture/community-cloud" },
            { text: "Security", link: "/security/" },
            {
              text: "GitHub",
              link: "https://github.com/CodeStrata/codestrata-engine",
            },
            { text: "Main Site", link: "https://codestrata.ai/" },
          ],
        },
      ],
    },
    socialLinks: [
      { icon: "github", link: "https://github.com/CodeStrata/codestrata-engine" },
    ],
    // Intentionally omit theme.footer — empty footer still mounts VitePress
    // VPFooter (full-width border mid-layout). CsFooter owns the footer via
    // the layout-bottom slot.
    //
    // Docs search: REMOVED FOR v0.2.0. VitePress local MiniSearch emits
    // `@localSearchIndex*` chunk filenames; Cloudflare Static Assets 307-redirects
    // `@` → `%40` and fails to serve the index, leaving a visible non-functional
    // Search control. Omit search entirely until a Cloudflare-safe asset path
    // exists (no Algolia / no new service for this release).
    outline: [2, 3],
  },
  sitemap: {
    hostname: "https://docs.codestrata.ai",
  },
});
