<script setup>
const year = new Date().getFullYear();
const SITE = "https://codestrata.ai";

/** External website destinations (match https://codestrata.ai footer). */
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
          Engineering Intelligence for Modern Software.
          Documentation for Community Engine, assessments, and IDE extensions.
        </div>
        <div>
          <h4>Product</h4>
          <ul>
            <li>
              <a :href="SITE + '/#how'" v-bind="extAttrs(SITE + '/#how')"
                >How it works</a
              >
            </li>
            <li>
              <a
                :href="SITE + '/sample-report'"
                v-bind="extAttrs(SITE + '/sample-report')"
                >Sample report</a
              >
            </li>
            <li>
              <a
                :href="SITE + '/approach'"
                v-bind="extAttrs(SITE + '/approach')"
                >Methodology</a
              >
            </li>
            <li>
              <a
                href="https://github.com/CodeStrata/codestrata-engine"
                target="_blank"
                rel="noopener noreferrer"
                >Open source engine</a
              >
            </li>
          </ul>
        </div>
        <div>
          <h4>Solutions</h4>
          <ul>
            <li>
              <a
                :href="SITE + '/for-private-equity'"
                v-bind="extAttrs(SITE + '/for-private-equity')"
                >Technical due diligence</a
              >
            </li>
            <li>
              <a
                :href="SITE + '/ecommerce-eol'"
                v-bind="extAttrs(SITE + '/ecommerce-eol')"
                >E-commerce EOL exposure</a
              >
            </li>
            <li>
              <a
                :href="SITE + '/#engage'"
                v-bind="extAttrs(SITE + '/#engage')"
                >Portfolio Scan</a
              >
            </li>
            <li>
              <a
                :href="SITE + '/#partner'"
                v-bind="extAttrs(SITE + '/#partner')"
                >Design partners</a
              >
            </li>
          </ul>
        </div>
        <div>
          <h4>Company</h4>
          <ul>
            <li>
              <a :href="SITE + '/#faq'" v-bind="extAttrs(SITE + '/#faq')"
                >FAQ</a
              >
            </li>
            <li>
              <a href="mailto:satish@codestrata.ai">Contact</a>
            </li>
            <li>
              <a
                :href="SITE + '/privacy'"
                v-bind="extAttrs(SITE + '/privacy')"
                >Privacy</a
              >
            </li>
          </ul>
        </div>
      </div>
      <div class="cs-footer__base">
        <span>© {{ year }} CodeStrata</span>
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
