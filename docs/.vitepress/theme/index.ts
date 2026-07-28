import DefaultTheme from "vitepress/theme";
import { h, watch, onMounted } from "vue";
import type { Theme } from "vitepress";
import { useData } from "vitepress";
import CsFooter from "./CsFooter.vue";
import "./custom.css";

function syncDataTheme(isDark: boolean) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute(
    "data-theme",
    isDark ? "dark" : "light",
  );
  // Match website theme-color for browser chrome
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute("content", isDark ? "#0b0d10" : "#ffffff");
  }
}

const Layout = {
  name: "CsLayout",
  setup() {
    const { isDark } = useData();
    onMounted(() => {
      syncDataTheme(isDark.value);
      watch(isDark, (v) => syncDataTheme(v));
    });
    return () =>
      h(DefaultTheme.Layout, null, {
        "layout-bottom": () => h(CsFooter),
      });
  },
};

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp() {
    // Theme CSS + tokens only; no Platform runtime.
  },
} satisfies Theme;
