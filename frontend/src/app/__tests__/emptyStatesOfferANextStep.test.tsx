/**
 * Every dead end on a screen has to tell the operator what to do next.
 *
 * `frontend/DESIGN.md` asks for two things: "an empty state naming the path it read plus
 * the CLI command to fix it", and "errors state what failed and which file, then what to
 * run". `test_console_commands_are_runnable.py` checks that the commands the console prints
 * are real. It cannot check that a command is printed at all -- so the cheapest way to
 * satisfy it is to print nothing, and one screen already did:
 *
 *   Run detail failed to load.
 *   run detail failed
 *   [ Retry ]
 *
 * for any run without a report, which is the normal state between step one and step two of
 * the documented loop. Retry re-fetched the same 404 forever, and the fix was one command
 * the screen never named.
 *
 * So this asserts presence. Each `EmptyState` must be one of three honest shapes:
 *
 *  1. a `failure-lab …` command in its detail, written there or held in a constant;
 *  2. a message from the loader, which the bridge is separately required to make
 *     actionable (`artifactBridge.test.ts` pins the remedy fields on a missing artifact);
 *  3. a no-match state whose action clears the filter that caused it -- there is no command
 *     to run, and the button is the next step;
 *  4. an *empty* state ("No …") naming the workspace path it read and found empty. DESIGN.md
 *     asks empty states for the path; a comparison with no case deltas has nothing to run.
 *
 * A *failure* state gets shapes 1 and 2 only. "It broke" with a path and no command is the
 * screen this file exists to prevent.
 */

import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.resolve(HERE, "../..");
const ROOTS = ["app/routes", "components/console"];

type Usage = { file: string; title: string; body: string; source: string };

/** Every `<EmptyState …>` in the console, with the source of its props. */
function emptyStates(): Usage[] {
  const found: Usage[] = [];
  for (const root of ROOTS) {
    const dir = path.join(SRC, root);
    for (const entry of readdirSync(dir)) {
      if (!entry.endsWith(".tsx")) continue;
      const text = readFileSync(path.join(dir, entry), "utf-8");
      let index = text.indexOf("<EmptyState");
      while (index !== -1) {
        // Props run to the matching `/>`; nested JSX in `action` uses `</`, so scan for the
        // first `/>` that is not inside a nested element.
        let depth = 0;
        let cursor = index + "<EmptyState".length;
        let end = text.length;
        while (cursor < text.length) {
          if (text.startsWith("/>", cursor)) {
            if (depth === 0) {
              end = cursor;
              break;
            }
            depth -= 1;
            cursor += 2;
            continue;
          }
          if (text.startsWith("</", cursor)) depth -= 1;
          else if (text[cursor] === "<") depth += 1;
          cursor += 1;
        }
        const body = text.slice(index, end);
        const title = /title=(?:"([^"]*)"|\{([^}]*)\})/.exec(body);
        found.push({
          file: `${root}/${entry}`,
          title: (title?.[1] ?? title?.[2] ?? "(dynamic)").trim(),
          body,
          source: text,
        });
        index = text.indexOf("<EmptyState", end);
      }
    }
  }
  return found;
}

const USAGES = emptyStates();

/** A message produced by a loader, which the bridge is required to make actionable. */
const FROM_LOADER = /\bstate\.message\b|State\.message\b|\bmessage\}/;
/** A no-match state: the next step is the button, not a command. */
const CLEARS_A_FILTER = /clear the .*filter|Clear filter|Clear filters/i;
/** A workspace path the screen read: `runs/…`, `reports/…`, `datasets/…`, `governance/…`. */
const NAMES_A_PATH = /(runs|reports|datasets|governance)\/[^\s"'`]/;

/**
 * True when the detail is (or resolves to) something holding a `failure-lab` command.
 *
 * `detail={GATE_COMMAND}` is as much a printed command as an inline string; keying on the
 * literal alone would have failed the one screen that factored its remedy into a constant,
 * which is the opposite of the behaviour this file rewards.
 */
function namesACommand(usage: Usage): boolean {
  if (usage.body.includes("failure-lab ")) return true;
  for (const identifier of usage.body.matchAll(/detail=\{([A-Z_][A-Z0-9_]*)\}/g)) {
    const declaration = new RegExp(
      `const\\s+${identifier[1]}\\s*=\\s*[^;]*failure-lab `,
    );
    if (declaration.test(usage.source)) return true;
  }
  return false;
}

describe("every empty and error state offers a next step", () => {
  it("finds the console's empty states", () => {
    expect(USAGES.length).toBeGreaterThanOrEqual(20);
  });

  it.each(USAGES.map((usage) => [`${usage.file} — ${usage.title}`, usage] as const))(
    "%s",
    (_label, usage) => {
      const isEmptyRatherThanBroken = /^No\b/.test(usage.title);
      const ok =
        namesACommand(usage) ||
        FROM_LOADER.test(usage.body) ||
        CLEARS_A_FILTER.test(usage.body) ||
        (isEmptyRatherThanBroken && NAMES_A_PATH.test(usage.body));

      expect(
        ok,
        `${usage.file} renders "${usage.title}" with no next step. Name the command that ` +
          `resolves it, relay the loader's message (the bridge is required to make those ` +
          `actionable), offer the control that clears the filter, or -- for an empty state ` +
          `only -- name the workspace path that came back empty.`,
      ).toBe(true);
    },
  );
});
