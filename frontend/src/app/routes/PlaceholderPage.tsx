import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type PlaceholderPageProps = {
  title: string;
  description: string;
};

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-primary">
          Route prepared
        </p>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">{title}</h2>
        <p className="max-w-2xl text-base leading-7 text-muted-foreground">{description}</p>
      </header>

      <Card className="bg-background/60">
        <CardHeader>
          <CardTitle>Waiting on later phase depth</CardTitle>
          <CardDescription>
            Phase 28 locks the route, navigation, and evidence scope. The detailed data experience
            lands in the next milestone phases without rewriting the shell.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm leading-6 text-muted-foreground">
          This placeholder is intentional. It preserves the React information architecture now so
          later comparison, failure, and run-drillthrough work can plug into a stable shell.
        </CardContent>
      </Card>
    </section>
  );
}
