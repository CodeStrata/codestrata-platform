/// <reference types="vite/client" />

declare const __INSIGHTS_BUILD_ID__: string;

interface ImportMetaEnv {
  readonly VITE_INSIGHTS_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
