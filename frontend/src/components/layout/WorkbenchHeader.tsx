import * as React from "react";

import { cn } from "@/lib/utils";

type WorkbenchHeaderProps = {
  meta?: React.ReactNode;
  title: string;
  description: React.ReactNode;
  supportingText?: React.ReactNode;
  aside?: React.ReactNode;
  className?: string;
};

export function WorkbenchHeader({
  meta,
  title,
  description,
  supportingText,
  aside,
  className,
}: WorkbenchHeaderProps) {
  return (
    <header
      className={cn(
        "grid gap-5 border-b border-border/70 pb-5",
        aside ? "xl:grid-cols-[minmax(0,1fr)_292px]" : undefined,
        className,
      )}
    >
      <div className="min-w-0 space-y-4">
        {meta ? <div className="flex flex-wrap items-center gap-2">{meta}</div> : null}
        <div className="space-y-3">
          <h2 className="text-[2.15rem] font-semibold leading-[1.02] tracking-[-0.06em] text-foreground sm:text-[2.4rem]">
            {title}
          </h2>
          <div className="max-w-3xl text-sm leading-6 text-muted-foreground">{description}</div>
          {supportingText ? (
            <div className="max-w-3xl text-sm leading-6 text-foreground">{supportingText}</div>
          ) : null}
        </div>
      </div>

      {aside ? (
        <aside className="rounded-[18px] border border-border/80 bg-background/55 p-4 text-sm leading-6 text-muted-foreground">
          {aside}
        </aside>
      ) : null}
    </header>
  );
}
