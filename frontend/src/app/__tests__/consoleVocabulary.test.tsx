/**
 * Predicates over the whole console, not assertions about one screen.
 *
 * Two findings survived a fix that was supposed to cover them, because the fix was verified
 * against its own example rather than generalised:
 *
 *  - `transitions.ts` was created so the console cannot hold a private opinion about what a
 *    regression is, and it is pinned to the engine's constants from both sides. But the pin
 *    covers the *module*, not its *use*, so `ExplorerPage` kept a hardcoded copy of the set
 *    through the consolidation that removed the other four.
 *  - Two printed remedy strings were corrected; six more were not. Those are covered by
 *    `tests/unit/test_console_commands_are_runnable.py`, which hands each printed command
 *    to the real argparse tree -- only Python can ask the CLI whether a command parses.
 *
 * This reads the source of every route and asserts the property, so a new screen that
 * hardcodes the vocabulary fails here rather than in front of an operator.
 */

import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { REGRESSION_TRANSITIONS } from "@/lib/artifacts/transitions";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.resolve(HERE, "../..");

function sourceFiles(): { name: string; text: string }[] {
  const roots = ["app/routes", "components/console", "components/layout"];
  const files: { name: string; text: string }[] = [];
  for (const root of roots) {
    const dir = path.join(SRC, root);
    for (const entry of readdirSync(dir)) {
      if (!entry.endsWith(".tsx") && !entry.endsWith(".ts")) continue;
      files.push({
        name: `${root}/${entry}`,
        text: readFileSync(path.join(dir, entry), "utf-8"),
      });
    }
  }
  return files;
}

describe("the console holds one copy of the engine's vocabulary", () => {
  it.each([...REGRESSION_TRANSITIONS])(
    "no screen hardcodes the transition literal %s",
    (transition) => {
      const offenders = sourceFiles()
        .filter(({ text }) => text.includes(`"${transition}"`))
        .map(({ name }) => name);
      expect(offenders, `${transition} is spelled out in a screen`).toEqual([]);
    },
  );

  it("keeps the literals in transitions.ts, where the engine contract pins them", () => {
    const module = readFileSync(path.join(SRC, "lib/artifacts/transitions.ts"), "utf-8");
    for (const transition of REGRESSION_TRANSITIONS) {
      expect(module).toContain(`"${transition}"`);
    }
  });
});
