import * as React from "react";

import { cn } from "@/lib/utils";

type WorkbenchSectionProps = {
  eyebrow?: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  aside?: React.ReactNode;
  className?: string;
  bodyClassName?: string;
  children: React.ReactNode;
};

export function WorkbenchSection({
  eyebrow,
  title,
  description,
  aside,
  className,
  bodyClassName,
  children,
}: WorkbenchSectionProps) {
  return (
    <section
      className={cn(
        "rounded-[20px] border border-border/70 bg-background/55",
        className,
      )}
    >
      <div
        className={cn(
          "grid gap-4 border-b border-border/70 px-4 py-4 lg:px-5",
          aside ? "xl:grid-cols-[minmax(0,1fr)_260px]" : undefined,
        )}
      >
        <div className="space-y-2">
          {eyebrow ? (
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              {eyebrow}
            </div>
          ) : null}
          <h3 className="text-[1.65rem] font-semibold tracking-[-0.05em] text-foreground">
            {title}
          </h3>
          {description ? (
            <div className="max-w-3xl text-sm leading-6 text-muted-foreground">{description}</div>
          ) : null}
        </div>

        {aside ? (
          <div className="rounded-[16px] border border-border/70 bg-card/45 px-4 py-3 text-sm leading-6 text-muted-foreground">
            {aside}
          </div>
        ) : null}
      </div>

      <div className={cn("px-4 py-4 lg:px-5", bodyClassName)}>{children}</div>
    </section>
  );
}
