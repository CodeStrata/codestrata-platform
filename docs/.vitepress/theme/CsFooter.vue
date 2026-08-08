<script setup>
const year = new Date().getFullYear();
const SITE = "https://codestrata.ai";

function extAttrs(href) {
  if (href.startsWith("mailto:")) {
    return {};
  }
  return { target: "_blank", rel: "noopener noreferrer" };
}
</script>

<template>
  <footer class="cs-footer" role="contentinfo">
    <div class="cs-footer__inner">
      <div class="cs-footer__grid">
        <div class="cs-footer__brand">
          <a
            class="cs-footer__brand-link"
            :href="SITE + '/'"
            target="_blank"
            rel="noopener noreferrer"
          >
            <strong>CodeStrata</strong>
          </a>
          Engineering decisions grounded in code. Community Edition
          documentation for Engine, assessments, reports, and VS Code.
        </div>
        <div>
          <h4>Docs</h4>
          <ul>
            <li><a href="/getting-started/">Getting Started</a></li>
            <li><a href="/getting-started/install">Installation</a></li>
            <li><a href="/reference/cli">CLI</a></li>
            <li><a href="/extensions/vscode">VS Code</a></li>
          </ul>
        </div>
        <div>
          <h4>Assess</h4>
          <ul>
            <li><a href="/assessments/">Running Assessments</a></li>
            <li><a href="/reports/">Assessment Reports</a></li>
            <li>
              <a href="/reports/engineering-intelligence"
                >Engineering Intelligence</a
              >
            </li>
            <li><a href="/troubleshooting/">Troubleshooting</a></li>
          </ul>
        </div>
        <div>
          <h4>Trust</h4>
          <ul>
            <li><a href="/security/privacy">Privacy</a></li>
            <li><a href="/reference/telemetry">Telemetry</a></li>
            <li><a href="/faq/">FAQ</a></li>
            <li>
              <a
                href="https://github.com/CodeStrata/codestrata-engine"
                target="_blank"
                rel="noopener noreferrer"
                >GitHub</a
              >
            </li>
            <li>
              <a :href="SITE + '/'" v-bind="extAttrs(SITE + '/')">codestrata.ai</a>
            </li>
          </ul>
        </div>
      </div>
      <div class="cs-footer__base">
        <span>© {{ year }} CodeStrata · Community Edition</span>
        <span>
          <a :href="SITE + '/'" target="_blank" rel="noopener noreferrer"
            >codestrata.ai</a
          >
          ·
          <a href="/" title="Documentation home">Docs home</a>
        </span>
      </div>
    </div>
  </footer>
</template>
