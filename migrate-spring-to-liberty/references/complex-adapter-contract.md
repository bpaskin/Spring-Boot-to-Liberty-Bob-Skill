# Complex Stack Adapter Contract

Load this reference whenever the analyzer detects a high- or critical-risk capability. Every complex adapter must use the same evidence lifecycle so that a migration can resume, compare behavior, or stop safely.

## Adapter interface

For each detected capability, complete these phases in order:

1. **DETECT** — cite dependency, source, configuration, test, and deployment evidence. Run `scripts/analyze_project.py` and confirm its findings through semantic inspection.
2. **CAPTURE** — record public behavior, data/protocol schemas, topology, ownership, concurrency, transaction, timeout, retry, security, shutdown, and recovery semantics.
3. **SELECT** — choose `DEDICATED_MODULE`, `RETAIN_LIBRARY`, `REDESIGN`, `STAGED_EXCEPTION`, or `REHOST`. Record the bounded files/modules and dependencies owned by the route.
4. **CHARACTERIZE** — generate `migration-characterization.json`; execute every applicable baseline positive, negative, outage, restart, and recovery case before changing the owned slice.
5. **GENERATE** — create only reviewable configuration and scaffolding. Keep secrets external, schema actions non-destructive, versions pinned, and generated changes separate from semantic code changes.
6. **MIGRATE** — change one bounded slice, compile it, and preserve independent blocked slices. Use safe codemods only for transformations whose semantics are invariant.
7. **VERIFY** — run the same cases on Liberty and grade baseline/target evidence with `scripts/verify_parity.py`.
8. **RECOVER** — test unavailable dependencies, retry exhaustion, restart, shutdown, and durable recovery. A successful happy-path test is insufficient.
9. **ROLL BACK OR CHECKPOINT** — revert only adapter-owned edits when safe, or leave a documented `PARTIAL`/`BLOCKED` checkpoint with an exact resume command.

## Required adapter output

Add one migration-ledger row per adapter containing:

| Field | Required value |
|---|---|
| Capability | Stable adapter identifier from `migration-inventory.json` |
| Boundary | Maven/Gradle modules, packages, configuration, data, and deployment resources owned by this slice |
| Baseline | Commands, results, behavior signatures, and artifact/log references |
| Route | One confirmed strategy and its trade-off |
| Generated files | Inventory, characterization contract, configuration scaffold, and codemod manifest as applicable |
| Positive cases | Named baseline and target cases |
| Failure/recovery cases | Named outage, overload, restart, redelivery, rollback, or fail-closed cases |
| Result | `PASS`, `PARTIAL`, or `BLOCKED` with the next resume point |

## Safe automation boundary

Automate discovery, schema validation, configuration scaffolding, approved namespace changes, and evidence grading. Do not automate a change that can alter ordering, transaction boundaries, backpressure, authorization, identity mapping, retry/DLQ behavior, data consistency, protocol compatibility, or recovery semantics without a confirmed contract.

## Commands

```bash
python3 migrate-spring-to-liberty/scripts/analyze_project.py . \
  --output migration-inventory.json
python3 migrate-spring-to-liberty/scripts/generate_characterization.py \
  --inventory migration-inventory.json \
  --output migration-characterization.json
python3 migrate-spring-to-liberty/scripts/safe_codemods.py .
python3 migrate-spring-to-liberty/scripts/verify_parity.py \
  --contract migration-characterization.json \
  --baseline evidence/baseline.json \
  --target evidence/target.json \
  --evidence-root evidence
```

The codemod command is a dry run unless both `--apply` and `--confirm-apply` are present. Review its manifest before applying it.
