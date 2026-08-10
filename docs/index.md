---
layout: home
title: Community Edition Documentation
description: Install CodeStrata Engine, run local Engineering Assessments, open reports, and use the VS Code extension — Community Edition only.

hero:
  name: Engineering decisions grounded in code.
  text: ""
  tagline: Community Edition documentation for CodeStrata Engine — local assessments, inspectable reports, and the VS Code extension.
  actions:
    - theme: brand
      text: Get Started
      link: /getting-started/
    - theme: alt
      text: Install Engine
      link: /getting-started/install
    - theme: alt
      text: VS Code Extension
      link: /extensions/vscode

features:
  - title: Install
    details: Install CodeStrata Engine, verify with codestrata version and doctor, then initialize a repository.
  - title: Assess
    details: Run deterministic Engineering Assessments locally with --no-ai, or opt into Engine-owned AI enrichment.
  - title: Reports
    details: Open HTML assessment reports and review findings, recommendations, and evidence boundaries.
  - title: VS Code
    details: Thin Engine client — discover CLI, run assessments, open local reports, and keep source local.
---

<div class="cs-home-below">

<p class="cs-eyebrow">Community journey</p>

<pre class="cs-journey">Install CodeStrata Engine
        ↓
Initialize repository configuration
        ↓
Run a local Engineering Assessment
        ↓
Review the HTML report in VS Code or browser</pre>

<p class="cs-eyebrow" style="margin-top:2.5rem">Start here</p>

<div class="cs-cta-grid">
  <a href="/getting-started/install">Installation <span>→</span></a>
  <a href="/getting-started/repository-initialization">Repository init <span>→</span></a>
  <a href="/getting-started/first-assessment">First assessment <span>→</span></a>
  <a href="/reports/">Assessment reports <span>→</span></a>
  <a href="/extensions/vscode">VS Code <span>→</span></a>
  <a href="/reference/cli">CLI reference <span>→</span></a>
  <a href="/security/privacy">Privacy <span>→</span></a>
  <a href="/faq/">FAQ <span>→</span></a>
</div>

<pre class="cs-terminal"><span class="c"># deterministic assessment (local)</span>
<span class="cmd">$</span> codestrata assess --repo . --no-ai
<span class="c">→ .codestrata-artifacts/assessments/&lt;repository-id&gt;/current/assessment.html</span></pre>

<div class="cs-callout" style="margin-top:1.5rem">
Deterministic Engineering Assessments are the default. Optional AI uses <strong>your</strong> provider credentials through the Engine — the VS Code extension does not send repository source to AI providers directly. This documentation covers <strong>Community Edition</strong> only.
</div>

</div>
