<script setup>
const year = new Date().getFullYear();
</script>

<template>
  <footer class="cs-footer" role="contentinfo">
    <div class="cs-footer__inner">
      <div class="cs-footer__grid">
        <div class="cs-footer__brand">
          <strong>CodeStrata</strong>
          Engineering Intelligence for Modern Software Organizations.
          Documentation for Community Engine, assessments, and IDE extensions.
        </div>
        <div>
          <h4>Product</h4>
          <ul>
            <li><a href="https://codestrata.ai/">Main site</a></li>
            <li><a href="https://codestrata.ai/platform">Platform</a></li>
            <li><a href="/engine/">Engine</a></li>
            <li><a href="/community/vs-platform">Community vs Platform</a></li>
          </ul>
        </div>
        <div>
          <h4>Documentation</h4>
          <ul>
            <li><a href="/getting-started/">Get Started</a></li>
            <li><a href="/reports/">Reports</a></li>
            <li><a href="/reference/cli">CLI</a></li>
            <li><a href="/troubleshooting/">Troubleshooting</a></li>
          </ul>
        </div>
        <div>
          <h4>Community</h4>
          <ul>
            <li>
              <a href="https://github.com/sknampally/codestrata-engine">Engine on GitHub</a>
            </li>
            <li><a href="/extensions/vscode">VS Code Extension</a></li>
            <li><a href="/extensions/cursor">Cursor Extension</a></li>
            <li><a href="/community/contributing">Contributing</a></li>
          </ul>
        </div>
      </div>
      <div class="cs-footer__base">
        <span>© {{ year }} CodeStrata</span>
        <span>
          <a href="/security/">Security</a>
          ·
          <a href="/security/privacy">Privacy</a>
          ·
          <a href="/security/support">Support</a>
        </span>
      </div>
    </div>
  </footer>
</template>
