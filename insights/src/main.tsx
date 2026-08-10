import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import { INSIGHTS_BUILD_ID } from "./buildId";
import "./designSystem/app.css";

const root = document.getElementById("root");
if (!root) {
  throw new Error("root_missing");
}

// Harmless deployment marker for owner Chrome validation (no secrets).
console.info(`[codestrata-insights] ${INSIGHTS_BUILD_ID}`);

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
