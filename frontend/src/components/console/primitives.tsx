import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

/** Uppercase section label — heading font, tracked out, muted. */
export function SectionLabel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "font-heading text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-ink",
        className,
      )}
    >
      {children}
    </div>
  );
}

export type ChipTone = "good" | "bad" | "warn" | "neutral" | "bad-strong";

const CHIP_TONES: Record<ChipTone, string> = {
  good: "bg-good-bg text-good",
  bad: "bg-bad-bg text-bad",
  warn: "bg-warn-bg text-warn",
  neutral: "bg-raised text-muted-ink",
  "bad-strong": "bg-bad-chip-bg text-bad-chip-ink",
};

/** Fully-rounded status chip — the one shape exception in both themes. */
export function StatusChip({
  tone,
  children,
  uppercase = false,
  className,
}: {
  tone: ChipTone;
  children: ReactNode;
  uppercase?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-[9px] py-[3px] font-body text-[11px]",
        uppercase && "text-[10px] font-semibold uppercase tracking-[0.1em]",
        CHIP_TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

/** Amber = partial/degraded run state; red stays reserved for regression. */
export function runStatusTone(status: string): ChipTone {
  const normalized = status.toLowerCase();
  if (normalized === "completed" || normalized === "complete") return "good";
  if (normalized === "partial" || normalized.includes("error") || normalized === "failed") {
    return "warn";
  }
  return "neutral";
}

/** Keyboard-reachable clickable row: Enter/Space activate, rows stay table rows. */
export function rowActivationProps(activate: () => void) {
  return {
    tabIndex: 0,
    onClick: activate,
    onKeyDown: (event: { key: string; preventDefault: () => void }) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        activate();
      }
    },
  };
}

type ConsoleButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
};

/** Two button styles only: primary (accent) and secondary (neutral outline). */
export function ConsoleButton({
  variant = "secondary",
  className,
  type = "button",
  ...props
}: ConsoleButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "cursor-pointer rounded-tok border px-[14px] py-2 font-body text-[13px] disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary"
          ? "border-accent bg-btn-bg text-btn-ink"
          : "border-line bg-transparent text-ink hover:bg-raised",
        className,
      )}
      {...props}
    />
  );
}

export function ConsoleInput({
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "rounded-tok border border-line bg-raised px-[10px] py-[7px] font-mono text-[12px] text-ink placeholder:text-muted-ink focus:border-accent focus:outline-none",
        className,
      )}
      {...props}
    />
  );
}

export type SegmentOption<T extends string> = {
  value: T;
  label: string;
};

/** Single bordered row; exactly one selected option (accent fill, ground text). */
export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className,
  "aria-label": ariaLabel,
}: {
  options: SegmentOption<T>[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
  "aria-label"?: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className={cn(
        "inline-flex overflow-hidden rounded-tok border border-line",
        className,
      )}
    >
      {options.map((option, index) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(option.value)}
            className={cn(
              "cursor-pointer border-y-0 border-r-0 px-3 py-1.5 font-body text-[12.5px]",
              index > 0 ? "border-l border-solid border-line" : "border-l-0",
              selected ? "bg-accent-fill text-on-accent" : "bg-transparent text-muted-ink",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

/** Standard route header: breadcrumb slot + H1 + right-aligned actions. */
export function RouteHeader({
  eyebrow,
  breadcrumb,
  title,
  actions,
  className,
}: {
  eyebrow?: ReactNode;
  breadcrumb?: ReactNode;
  title: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "flex items-end justify-between gap-6 border-b border-line px-7 pb-[15px] pt-[22px]",
        className,
      )}
    >
      <div className="min-w-0">
        {breadcrumb}
        {eyebrow ? <SectionLabel className="tracking-[0.2em]">{eyebrow}</SectionLabel> : null}
        <h1 className="mt-1.5 font-heading text-[28px] font-semibold leading-[1.1] text-ink">
          {title}
        </h1>
      </div>
      {actions ? <div className="flex flex-none gap-2">{actions}</div> : null}
    </header>
  );
}

export function TableHeadCell({
  children,
  align = "left",
  className,
}: {
  children?: ReactNode;
  align?: "left" | "right" | "center";
  className?: string;
}) {
  return (
    <th
      className={cn(
        "px-2 py-[9px] text-[10.5px] font-normal uppercase tracking-[0.1em] text-muted-ink",
        align === "right" && "text-right",
        align === "center" && "text-center",
        align === "left" && "text-left",
        className,
      )}
    >
      {children}
    </th>
  );
}

/** Empty / no-match states. Empty names the path read; no-match names the filter to clear. */
export function EmptyState({
  title,
  detail,
  action,
}: {
  title: string;
  detail: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="mt-6 rounded-tok border border-line bg-panel px-5 py-6">
      <div className="font-body text-[13.5px] text-ink">{title}</div>
      <div className="mt-1.5 font-mono text-[11.5px] leading-relaxed text-muted-ink">{detail}</div>
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}

const SIGNED_FORMAT = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  signDisplay: "always",
});

/** Signed delta, one decimal, minus sign rendered as a true minus. */
export function formatSignedPts(value: number): string {
  return SIGNED_FORMAT.format(value).replace("-", "−");
}

export function formatPercent(value: number | null): string {
  if (value === null) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

export function formatScore(value: number): string {
  return value.toFixed(3);
}

/** Signed three-decimal score with a true minus sign. */
export function formatSignedScore(value: number): string {
  const magnitude = Math.abs(value).toFixed(3);
  if (value < 0) return `−${magnitude}`;
  if (value > 0) return `+${magnitude}`;
  return magnitude;
}

/**
 * Run ids are `%Y%m%d_%H%M%S[_micro]_slug_hash`; the timestamp prefix repeats
 * row to row, so mute it and let the eye land on the distinguishing slug.
 */
export function RunIdText({ runId }: { runId: string }) {
  const match = runId.match(/^(\d{8}_\d{6}(?:_\d+)?_)(.+)$/);
  if (!match) return <>{runId}</>;
  return (
    <>
      <span className="font-normal text-muted-ink">{match[1]}</span>
      {match[2]}
    </>
  );
}

/** Run ids keep their raw form; ellipsis-truncate only in tight contexts. */
export function truncateRunId(runId: string): string {
  const parts = runId.split("_");
  if (parts.length <= 2) return runId;
  return `…_${parts.slice(-2).join("_")}`;
}

export function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const month = date.toLocaleString("en-US", { month: "short" });
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${month} ${date.getDate()}, ${hours}:${minutes}`;
}
