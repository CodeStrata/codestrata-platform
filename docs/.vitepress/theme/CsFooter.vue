<script setup>
import { computed } from "vue";
import { useData } from "vitepress";

const year = new Date().getFullYear();
const { page } = useData();

/** Large marketing footer only on the docs home; inner pages use sidebar Trust links. */
const isHome = computed(() => {
  const path = page.value?.relativePath || "";
  return path === "index.md" || path === "";
});
</script>

<template>
  <footer v-if="isHome" class="cs-footer" role="contentinfo">
    <div class="cs-footer__inner">
      <div class="cs-footer__grid">
        <div class="cs-footer__brand">
          <a class="cs-footer__brand-link" href="/">
            <strong>CodeStrata Docs</strong>
          </a>
          Engineering decisions grounded in code. Community Edition
          documentation for Engine, assessments, reports, and VS Code.
        </div>
        <div>
          <h4>Docs</h4>
          <ul>
            <li><a href="/getting-started/">Getting Started</a></li>
            <li><a href="/reference/cli">CLI</a></li>
            <li><a href="/extensions/vscode">VS Code</a></li>
            <li><a href="/assessments/">Assessments</a></li>
          </ul>
        </div>
        <div>
          <h4>Trust</h4>
          <ul>
            <li><a href="/security/privacy">Privacy</a></li>
            <li><a href="/security/">Security</a></li>
            <li><a href="/reference/telemetry">Telemetry</a></li>
            <li>
              <a
                href="https://github.com/CodeStrata/codestrata-engine"
                target="_blank"
                rel="noopener noreferrer"
                >GitHub</a
              >
            </li>
          </ul>
        </div>
        <div>
          <h4>Company</h4>
          <ul>
            <li>
              <a
                href="https://codestrata.ai/"
                target="_blank"
                rel="noopener noreferrer"
                >Main Site</a
              >
            </li>
            <li><a href="/faq/">FAQ</a></li>
            <li><a href="/reference/release-notes">Release Notes</a></li>
          </ul>
        </div>
      </div>
      <div class="cs-footer__base">
        <span>© {{ year }} CodeStrata · Community Edition</span>
        <span>
          <a href="/" title="Documentation home">Docs home</a>
          ·
          <a
            href="https://codestrata.ai/"
            target="_blank"
            rel="noopener noreferrer"
            >codestrata.ai</a
          >
        </span>
      </div>
    </div>
  </footer>
  <footer v-else class="cs-footer cs-footer--minimal" role="contentinfo">
    <div class="cs-footer__inner cs-footer__inner--minimal">
      <span>© {{ year }} CodeStrata · Community Edition</span>
      <span>
        <a href="/security/privacy">Privacy</a>
        ·
        <a href="https://codestrata.ai/" target="_blank" rel="noopener noreferrer"
          >Main Site</a
        >
      </span>
    </div>
  </footer>
</template>
