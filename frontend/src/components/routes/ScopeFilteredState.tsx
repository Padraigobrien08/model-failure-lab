import { ScopeStateNotice } from "@/components/raw-debug/ScopeStateNotice";

type ScopeFilteredStateProps =
  | {
      state: "scope-hidden";
      title: string;
      message: string;
      recoveryPath: string;
      testId?: string;
    }
  | {
      state: "missing";
      title: string;
      message: string;
      testId?: string;
    };

export function ScopeFilteredState(props: ScopeFilteredStateProps) {
  return (
    <div data-testid={props.testId}>
      <ScopeStateNotice {...props} />
    </div>
  );
}
