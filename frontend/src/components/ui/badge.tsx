import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeTone = "default" | "accent" | "exploratory" | "muted";

const toneClasses: Record<BadgeTone, string> = {
  default: "bg-foreground/10 text-foreground",
  accent: "bg-primary/15 text-primary",
  exploratory: "border border-dashed border-primary/40 bg-primary/10 text-primary",
  muted: "bg-muted text-muted-foreground",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em]",
        toneClasses[tone],
        className,
      )}
      {...props}
    />
  );
}
