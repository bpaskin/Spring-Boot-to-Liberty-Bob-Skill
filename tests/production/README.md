# Production integration evidence

[`scenarios.json`](scenarios.json) defines the minimum positive and failure cases for database/XA/schema, identity/observability, and Kafka/deployment migrations. The classifier fixtures named by the manifest are raw Spring inputs used to test detection; they are not substitutes for running a migrated application against real services.

Run `run_production_evals.py --mode evidence --evidence-root <directory>` only after executing every case in an isolated disposable or approved target environment. The evidence directory must contain `<scenario>.json` plus every referenced non-empty log/artifact. A missing service is `BLOCKED`, not `PASS`.

Validate the pinned disposable service definitions without starting containers:

```bash
python3 migrate-spring-to-liberty/scripts/run_integration_lab.py --mode static
```

Starting a lab requires `--confirm-disposable`, a named scenario, and an evidence directory. The runner uses random project ownership, ephemeral credentials, random host ports, bounded waits, failure logs, and unconditional volume cleanup. Pass an application test as `--test-command-json '["executable", "arg"]'` with `--test-cwd`; the command receives resolved non-secret `LAB_*` endpoints and ephemeral credentials through its environment. The lab proves only the cases executed by that command; run every required positive and failure case before grading production evidence.

Evidence shape:

```json
{
  "scenario": "postgres-xa-schema",
  "environment": {
    "liberty_version": "<exact version>",
    "java_version": "<exact version>",
    "infrastructure": "<products, versions, and isolation boundary>",
    "executed_at": "<ISO-8601 timestamp>",
    "command": "<reproducible test command>"
  },
  "cases": [
    {
      "name": "commit-both-resources",
      "status": "PASS",
      "observed": "<asserted external behavior and durable side effects>",
      "artifact": "postgres-xa-schema/commit-both-resources.log"
    }
  ]
}
```

Artifact paths must be relative to the evidence root and cannot use `..`. The grader rejects empty/missing artifacts, incomplete environment metadata, missing observed results, and every status other than `PASS`.
