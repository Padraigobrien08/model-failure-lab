import type { MethodRouteExplanationSection } from "@/lib/methodRoute";

type MethodExplanationProps = {
  sections: MethodRouteExplanationSection[];
};

export function MethodExplanation({ sections }: MethodExplanationProps) {
  return (
    <section aria-label="Method explanation" className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/70 pb-2">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Method explanation
        </h2>
        <p className="text-xs text-muted-foreground">Structured status rationale</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {sections.map((section) => (
          <section key={section.title} className="space-y-3 border-l border-border/70 pl-4">
            <h3 className="text-sm font-semibold text-foreground">{section.title}</h3>
            <ul className="space-y-2 text-sm leading-6 text-muted-foreground">
              {section.bullets.map((bullet) => (
                <li key={bullet} className="list-none">
                  {bullet}
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </section>
  );
}
