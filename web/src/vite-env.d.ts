/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SCORPIO_COORDINATOR_URL: string;
  readonly VITE_SCORPIO_TENANT_ID: string;
  readonly VITE_SCORPIO_AUTH_BEARER: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
