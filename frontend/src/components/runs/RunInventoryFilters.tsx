import { Search } from "lucide-react";

type RunInventoryFiltersProps = {
  search: string;
  dataset: string;
  model: string;
  status: string;
  datasetOptions: string[];
  modelOptions: string[];
  statusOptions: string[];
  onSearchChange: (value: string) => void;
  onDatasetChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onClear: () => void;
};

type FilterSelectProps = {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
};

function FilterSelect({ label, value, options, onChange }: FilterSelectProps) {
  return (
    <label className="flex min-w-[11rem] flex-col gap-2">
      <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </span>
      <select
        aria-label={label}
        className="h-11 rounded-full border border-border/70 bg-card/80 px-4 text-sm text-foreground outline-none transition-colors focus:border-primary/40"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

export function RunInventoryFilters({
  search,
  dataset,
  model,
  status,
  datasetOptions,
  modelOptions,
  statusOptions,
  onSearchChange,
  onDatasetChange,
  onModelChange,
  onStatusChange,
  onClear,
}: RunInventoryFiltersProps) {
  return (
    <section className="rounded-[24px] border border-border/70 bg-card/70 p-4">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[minmax(0,1.4fr)_repeat(3,minmax(11rem,1fr))]">
          <label className="flex min-w-[16rem] flex-col gap-2">
            <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Run id
            </span>
            <div className="flex h-11 items-center gap-3 rounded-full border border-border/70 bg-card/80 px-4">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                aria-label="Run id search"
                className="w-full bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
                placeholder="Search run id"
                type="search"
                value={search}
                onChange={(event) => onSearchChange(event.target.value)}
              />
            </div>
          </label>

          <FilterSelect
            label="Dataset"
            value={dataset}
            options={datasetOptions}
            onChange={onDatasetChange}
          />
          <FilterSelect
            label="Model"
            value={model}
            options={modelOptions}
            onChange={onModelChange}
          />
          <FilterSelect
            label="Status"
            value={status}
            options={statusOptions}
            onChange={onStatusChange}
          />
        </div>

        <button
          type="button"
          className="h-11 rounded-full border border-border/70 bg-background/70 px-5 text-sm font-semibold text-foreground transition-colors hover:bg-background"
          onClick={onClear}
        >
          Clear filters
        </button>
      </div>
    </section>
  );
}
