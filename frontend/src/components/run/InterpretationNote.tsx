type InterpretationNoteProps = {
  note: string;
};

export function InterpretationNote({ note }: InterpretationNoteProps) {
  return (
    <section aria-label="Run interpretation" className="space-y-2 border-b border-border/70 pb-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Interpretation
        </h2>
        <p className="text-xs text-muted-foreground">Single-run read</p>
      </div>
      <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{note}</p>
    </section>
  );
}
