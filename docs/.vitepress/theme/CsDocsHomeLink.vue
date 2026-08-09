<script setup lang="ts">
import { onMounted, watch } from "vue";
import { useRoute } from "vitepress";

const DOCS_HOME = "/";

function wireLogoLink() {
  if (typeof document === "undefined") return;
  const title = document.querySelector(".VPNavBarTitle");
  if (!title) return;
  const anchor = title.querySelector("a.title, a");
  if (!anchor) return;
  // Docs brand mark → documentation home (not the company website).
  anchor.setAttribute("href", DOCS_HOME);
  anchor.removeAttribute("target");
  anchor.removeAttribute("rel");
  anchor.setAttribute("aria-label", "CodeStrata Docs home");
  anchor.setAttribute("title", "CodeStrata Docs home");
}

const route = useRoute();
onMounted(() => {
  wireLogoLink();
  watch(
    () => route.path,
    () => {
      requestAnimationFrame(wireLogoLink);
    },
  );
});
</script>

<template>
  <!-- Logo already provides Docs home; keep Main Site only in primary nav. -->
  <span class="cs-nav-docs-home" aria-hidden="true"></span>
</template>
