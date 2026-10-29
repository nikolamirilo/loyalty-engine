import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    // Same mapping as tsconfig.json's "@/*": ["./*"].
    alias: { "@": fileURLToPath(new URL(".", import.meta.url)) },
  },
  test: {
    // The tested modules are server-side or plain functions; none need a DOM.
    environment: "node",
    include: ["**/*.test.ts"],
    env: {
      // lib/auth/config.ts refuses to load without these. Test-only values.
      ADMIN_USERNAME: "test-admin",
      ADMIN_PASSWORD: "test-password",
      AUTH_SECRET: "test-secret-not-used-anywhere-else",
      // Date formatting reads the local zone, so pin it.
      TZ: "UTC",
    },
  },
});
