import { Link } from "react-router-dom";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ScopeStateNoticeProps =
  | {
      state: "scope-hidden";
      title: string;
      message: string;
      recoveryPath: string;
    }
  | {
      state: "missing";
      title: string;
      message: string;
    };

export function ScopeStateNotice(props: ScopeStateNoticeProps) {
  const isMissing = props.state === "missing";

  return (
    <section className="space-y-3 border border-border/70 bg-muted/10 p-4">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          {isMissing ? "Missing entity" : "Scope warning"}
        </p>
        <h2 className="text-lg font-semibold tracking-[-0.03em] text-foreground">{props.title}</h2>
      </div>
      <p className="text-sm leading-6 text-muted-foreground">{props.message}</p>
      {props.state === "scope-hidden" ? (
        <Link
          className={cn(buttonVariants({ size: "sm", variant: "default" }))}
          to={props.recoveryPath}
        >
          Include exploratory
        </Link>
      ) : null}
    </section>
  );
}
