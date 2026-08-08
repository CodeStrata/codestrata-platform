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
      alt: "CodeStrata",
    },
    logoLink: "https://codestrata.ai/",
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
          { text: "Telemetry", link: "/reference/telemetry" },
          { text: "Privacy", link: "/security/privacy" },
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
            { text: "Telemetry", link: "/reference/telemetry" },
            { text: "Privacy", link: "/security/privacy" },
            { text: "Security", link: "/security/" },
            { text: "Community API", link: "/reference/api" },
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
