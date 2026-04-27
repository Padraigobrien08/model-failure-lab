# Fixture Workspace

Generate a deterministic local workspace for UI and analysis smoke testing:

```bash
python3 scripts/generate_insight_fixture.py
```

Default output:

- `artifacts/insight-fixture-workspace`

Then point the React debugger at that root:

```bash
export FAILURE_LAB_ARTIFACT_ROOT="$(pwd)/artifacts/insight-fixture-workspace"
npm --prefix frontend run dev
```
