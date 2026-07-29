import { defineConfig } from "vitepress";

/**
 * CodeStrata public documentation portal.
 * Canonical public URL: https://docs.codestrata.ai
 * Local/preview builds keep base `/` — deployment sets the domain.
 */
export default defineConfig({
  title: "CodeStrata Docs",
  description:
    "Engineering Intelligence for Modern Software — CodeStrata Engine, assessments, reports, and IDE extensions.",
  lang: "en-US",
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: false,
  /**
   * Theme: dark-first brand default; users can switch to light.
   * `true` enables prefers-color-scheme when no stored preference (system).
   * Preference persists in localStorage (`vitepress-theme-appearance`).
   */
  appearance: true,
  // Keep repo policy / meta files at docs/ root without colliding with section routes
  // (e.g. SECURITY.md vs security/).
  srcExclude: [
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "PRIVACY.md",
    "SUPPORT.md",
    "CONTRIBUTING.md",
    "VISUAL_REGRESSION.md",
    "**/node_modules/**",
  ],
  head: [
    ["link", { rel: "icon", href: "/favicon.svg", type: "image/svg+xml" }],
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
    ["meta", { name: "theme-color", content: "#0b0d10" }],
    ["meta", { property: "og:type", content: "website" }],
    ["meta", { property: "og:title", content: "CodeStrata Docs" }],
    [
      "meta",
      {
        property: "og:description",
        content:
          "Engineering Intelligence for Modern Software. Assess repositories with CodeStrata Engine.",
      },
    ],
    ["meta", { property: "og:url", content: "https://docs.codestrata.ai/" }],
    ["meta", { name: "twitter:card", content: "summary" }],
  ],
  markdown: {
    // High-contrast dark blocks in both appearance modes (website code surfaces stay dark).
    theme: {
      light: "github-dark",
      dark: "github-dark",
    },
  },
  themeConfig: {
    logo: {
      light: "/brand/lockup-horizontal-on-light.svg",
      dark: "/brand/lockup-horizontal-on-dark.svg",
      alt: "CodeStrata",
    },
    // Logo click is wired to https://codestrata.ai/ (new tab) in CsDocsHomeLink.
    // Keep a sensible fallback for no-JS crawlers.
    logoLink: "https://codestrata.ai/",
    siteTitle: false,
    nav: [
      { text: "Get Started", link: "/getting-started/" },
      { text: "Engine", link: "/engine/" },
      { text: "Assessments", link: "/assessments/" },
      { text: "Reports", link: "/reports/" },
      {
        text: "Extensions",
        items: [
          { text: "VS Code Extension", link: "/extensions/vscode" },
          { text: "Cursor Extension", link: "/extensions/cursor" },
        ],
      },
      { text: "AI Providers", link: "/ai-providers/" },
      {
        text: "Reference",
        items: [
          { text: "CLI", link: "/reference/cli" },
          { text: "Configuration", link: "/reference/configuration" },
          { text: "JSON Reports", link: "/reference/json-reports" },
          { text: "Findings", link: "/reference/findings" },
          { text: "Public API", link: "/reference/api" },
          { text: "MCP", link: "/reference/mcp" },
          { text: "Compatibility", link: "/reference/compatibility" },
          { text: "Release Notes", link: "/reference/release-notes" },
        ],
      },
      {
        text: "Community",
        items: [
          { text: "Community vs Platform", link: "/community/vs-platform" },
          { text: "Examples", link: "/community/examples" },
          { text: "Contributing", link: "/community/contributing" },
          { text: "Troubleshooting", link: "/troubleshooting/" },
        ],
      },
      { text: "Platform", link: "/platform/" },
      {
        text: "Main Site",
        link: "https://codestrata.ai/",
      },
    ],
    sidebar: {
      "/getting-started/": [
        {
          text: "Getting Started",
          items: [
            { text: "Overview", link: "/getting-started/" },
            { text: "Prerequisites", link: "/getting-started/prerequisites" },
            { text: "Install Engine", link: "/getting-started/install" },
            { text: "First Assessment", link: "/getting-started/first-assessment" },
            { text: "Next Steps", link: "/getting-started/next-steps" },
          ],
        },
      ],
      "/engine/": [
        {
          text: "CodeStrata Engine",
          items: [
            { text: "Overview", link: "/engine/" },
            { text: "Installation", link: "/engine/installation" },
            { text: "Doctor", link: "/engine/doctor" },
          ],
        },
      ],
      "/assessments/": [
        {
          text: "Engineering Assessments",
          items: [
            { text: "Overview", link: "/assessments/" },
            { text: "Deterministic vs AI", link: "/assessments/deterministic-vs-ai" },
          ],
        },
      ],
      "/reports/": [
        {
          text: "Understanding Reports",
          items: [
            { text: "Overview", link: "/reports/" },
            { text: "Findings & Recommendations", link: "/reports/findings" },
          ],
        },
      ],
      "/extensions/": [
        {
          text: "IDE Extensions",
          items: [
            { text: "Overview", link: "/extensions/" },
            { text: "VS Code", link: "/extensions/vscode" },
            { text: "Cursor", link: "/extensions/cursor" },
          ],
        },
      ],
      "/ai-providers/": [
        {
          text: "AI Providers",
          items: [{ text: "Overview", link: "/ai-providers/" }],
        },
      ],
      "/reference/": [
        {
          text: "Reference",
          items: [
            { text: "CLI", link: "/reference/cli" },
            { text: "Configuration", link: "/reference/configuration" },
            { text: "JSON Reports", link: "/reference/json-reports" },
            { text: "Findings", link: "/reference/findings" },
            { text: "Public API", link: "/reference/api" },
            { text: "MCP", link: "/reference/mcp" },
            { text: "Public Contracts", link: "/reference/public-contracts" },
            { text: "Compatibility", link: "/reference/compatibility" },
            { text: "Release Notes", link: "/reference/release-notes" },
          ],
        },
      ],
      "/community/": [
        {
          text: "Community",
          items: [
            { text: "Community vs Platform", link: "/community/vs-platform" },
            { text: "Examples", link: "/community/examples" },
            { text: "Contributing", link: "/community/contributing" },
          ],
        },
      ],
      "/security/": [
        {
          text: "Security & Privacy",
          items: [
            { text: "Security", link: "/security/" },
            { text: "Privacy", link: "/security/privacy" },
            { text: "Responsible Disclosure", link: "/security/disclosure" },
            { text: "Support", link: "/security/support" },
          ],
        },
      ],
      "/troubleshooting/": [
        {
          text: "Troubleshooting",
          items: [{ text: "Common issues", link: "/troubleshooting/" }],
        },
      ],
      "/platform/": [
        {
          text: "Platform",
          items: [{ text: "Overview", link: "/platform/" }],
        },
      ],
    },
    socialLinks: [
      { icon: "github", link: "https://github.com/CodeStrata/codestrata-engine" },
    ],
    footer: {
      message: "",
      copyright: "",
    },
    search: {
      provider: "local",
    },
    outline: [2, 3],
  },
  sitemap: {
    hostname: "https://docs.codestrata.ai",
  },
});
