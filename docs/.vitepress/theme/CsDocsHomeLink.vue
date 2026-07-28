<script setup lang="ts">
import { onMounted, watch } from "vue";
import { useRoute } from "vitepress";

const SITE = "https://codestrata.ai/";

function wireLogoLink() {
  if (typeof document === "undefined") return;
  const title = document.querySelector(".VPNavBarTitle");
  if (!title) return;
  const anchor = title.querySelector("a.title, a");
  if (!anchor) return;
  // Ensure logo is not wrapping unrelated nav controls.
  anchor.setAttribute("href", SITE);
  anchor.setAttribute("target", "_blank");
  anchor.setAttribute("rel", "noopener noreferrer");
  anchor.setAttribute("aria-label", "CodeStrata website (opens in a new tab)");
  anchor.setAttribute("title", "CodeStrata website");
}

const route = useRoute();
onMounted(() => {
  wireLogoLink();
  watch(
    () => route.path,
    () => {
      // VitePress may re-render the title link on navigation.
      requestAnimationFrame(wireLogoLink);
    },
  );
});
</script>

<template>
  <div class="cs-nav-docs-home">
    <a
      class="cs-docs-home"
      href="/"
      aria-label="Documentation home"
      title="Documentation home"
    >
      <svg
        class="cs-docs-home__icon"
        viewBox="0 0 24 24"
        width="18"
        height="18"
        aria-hidden="true"
        focusable="false"
      >
        <path
          fill="currentColor"
          d="M12 3.2 3.8 10.2c-.3.25-.3.7 0 .95l.7.55c.28.22.68.2.94-.05L12 5.9l6.56 5.75c.26.25.66.27.94.05l.7-.55c.3-.25.3-.7 0-.95L12 3.2Zm6.2 8.3v7.1c0 .55-.45 1-1 1h-3.4c-.33 0-.6-.27-.6-.6v-3.7c0-.55-.45-1-1-1h-1.4c-.55 0-1 .45-1 1v3.7c0 .33-.27.6-.6.6H6.8c-.55 0-1-.45-1-1v-7.1l6.2-5.4 6.2 5.4Z"
        />
      </svg>
      <span class="cs-docs-home__label">Docs</span>
    </a>
  </div>
</template>
