import fsSync from "node:fs";
import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

import { failureLabArtifactsPlugin } from "./server/artifactBridge";

/**
 * The console's version label, read from the package's own metadata at build time.
 *
 * It used to be a hardcoded string in ConsoleShell.tsx, which drifted immediately: the shell
 * said v0.10.0 while pyproject said 0.10.1 and the README screenshots said v0.9.0. A tool
 * whose product is artifact provenance should not misreport its own version.
 */
function resolvePackageVersion(): string {
  const pyproject = path.resolve(__dirname, "..", "pyproject.toml");
  try {
    const match = fsSync
      .readFileSync(pyproject, "utf-8")
      .match(/^\s*version\s*=\s*"([^"]+)"/m);
    if (match) {
      return match[1];
    }
  } catch {
    // Fall through: a missing pyproject means the console is running outside a checkout.
  }
  return "unknown";
}

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(resolvePackageVersion()),
  },
  plugins: [
    react(),
    failureLabArtifactsPlugin({ repoRoot: path.resolve(__dirname, "..") }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5174,
  },
  preview: {
    port: 5174,
  },
});
