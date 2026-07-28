---
layout: home
title: Engineering Intelligence for Modern Software
description: Engineering Intelligence for Modern Software — CodeStrata Engine, assessments, reports, and IDE extensions.

hero:
  name: Engineering Intelligence for Modern Software
  text: ""
  tagline: Understand, assess, modernize, and transform software systems with confidence — starting with deterministic Engineering Assessments.
  actions:
    - theme: brand
      text: Get Started
      link: /getting-started/
    - theme: alt
      text: Install the Engine
      link: /getting-started/install
    - theme: alt
      text: View GitHub
      link: https://github.com/sknampally/codestrata-engine

features:
  - title: Install Engine
    details: Install CodeStrata Engine with pip, a venv, or from source — then verify with codestrata version and doctor.
  - title: First Assessment
    details: Run a deterministic Engineering Assessment with --no-ai and open the HTML report.
  - title: Understand Reports
    details: Read findings, recommendations, and evidence in the Strata-style Engineering Assessment report.
  - title: VS Code
    details: Thin Engine client — findings, recommendations, diagnostics, and report access in the editor.
  - title: Cursor
    details: Ground Chat and Agent with assessment artifacts and .cursor/rules/codestrata-engineering.mdc.
  - title: CLI · API · MCP
    details: Community CLI journey commands, public contracts, and optional MCP — Platform stays separate.
---

<div class="cs-home-below">

<p class="cs-eyebrow">01 // PRIMARY JOURNEY</p>

<pre class="cs-journey">Install CodeStrata Engine
        ↓
Assess a repository
        ↓
Review findings and recommendations
        ↓
Use VS Code or Cursor integration</pre>

<p class="cs-eyebrow" style="margin-top:2.5rem">02 // START HERE</p>

<div class="cs-cta-grid">
  <a href="/getting-started/install">Install <span>→</span></a>
  <a href="/getting-started/first-assessment">First Assessment <span>→</span></a>
  <a href="/reports/">Understand Reports <span>→</span></a>
  <a href="/extensions/vscode">VS Code <span>→</span></a>
  <a href="/extensions/cursor">Cursor <span>→</span></a>
  <a href="/reference/cli">CLI <span>→</span></a>
  <a href="/reference/api">API and MCP <span>→</span></a>
  <a href="/troubleshooting/">Troubleshooting <span>→</span></a>
</div>

<pre class="cs-terminal"><span class="c"># deterministic by default</span>
<span class="cmd">$</span> codestrata assess --repo . --output reports --no-ai
<span class="c">→ reports/&lt;repo&gt;/&lt;timestamp&gt;/report.html</span></pre>

<div class="cs-callout" style="margin-top:1.5rem">
Deterministic Engineering Intelligence is the default. Optional AI uses <strong>your</strong> provider credentials — AI is a capability, not the product name. Platform capabilities are commercial and separate — see <a href="/community/vs-platform">Community vs Platform</a>.
</div>

</div>
