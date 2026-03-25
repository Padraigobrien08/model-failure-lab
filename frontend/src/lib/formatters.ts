export function formatLabel(value: string | null | undefined) {
  if (!value) {
    return "Unknown";
  }

  const acronyms: Record<string, string> = {
    ece: "ECE",
    id: "ID",
    ood: "OOD",
    tfidf: "TF-IDF",
    dro: "DRO",
  };

  return value
    .split(/[_-\s]+/)
    .filter(Boolean)
    .map((part) => {
      const normalized = part.toLowerCase();
      if (acronyms[normalized]) {
        return acronyms[normalized];
      }

      return part.charAt(0).toUpperCase() + part.slice(1);
    })
    .join(" ");
}

export function formatCount(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatMetric(value: number | null | undefined, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }

  return value.toFixed(digits);
}

export function formatSignedMetric(value: number | null | undefined, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }

  const formatted = value.toFixed(digits);
  if (value > 0) {
    return `+${formatted}`;
  }

  return formatted;
}

export function formatComparisonMode(mode: string | null | undefined) {
  if (mode === "baseline_metric") {
    return "Reference lane";
  }

  if (mode === "delta_vs_baseline") {
    return "Δ vs baseline";
  }

  return formatLabel(mode);
}

export function getMetricTextTone(
  value: number | null | undefined,
  invertPolarity = false,
  comparisonMode?: string,
) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(value) ||
    comparisonMode === "baseline_metric"
  ) {
    return "text-foreground";
  }

  const normalized = invertPolarity ? -value : value;
  if (normalized > 0) {
    return "text-primary";
  }

  if (normalized < 0) {
    return "text-destructive";
  }

  return "text-foreground";
}
