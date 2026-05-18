// Licensed under the Apache License, Version 2.0 (see LICENSE in repository root).

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
