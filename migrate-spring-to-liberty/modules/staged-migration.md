# Module: Staged Migration Orchestrator

Follow the [complex adapter contract](../references/complex-adapter-contract.md) and shared [migration ledger](../references/migration-ledger.md). Use this module when the contract selects a staged migration or when a supported Spring Boot application contains a critical stack whose complete rewrite cannot be proven in one transaction.

## Default sequence for complex applications

1. Rehost the unchanged Spring Boot 3/4 application on Liberty when eligible.
2. Establish baseline-versus-Liberty behavior parity before removing any Spring capability.
3. Build a dependency graph of Maven/Gradle modules, packages, runtime configuration, external resources, schemas, and deployment artifacts.
4. Select one bounded slice whose public behavior and dependencies can be characterized independently.
5. Migrate, compile, run Liberty, and verify that slice while preserving all excluded Spring files and dependencies.
6. Remove Spring dependencies only when no retained slice uses them.
7. Repeat until the requested boundary is complete or a blocker is recorded.

Do not mix a Boot rehost and Jakarta rewrite in the same deployable artifact unless the contract names the interoperability model and a runtime test proves it. Prefer separate deployables or a clearly isolated library boundary when framework lifecycles would otherwise overlap.

## Slice contract

Record for every slice:

- stable slice ID and business capability;
- owning Maven/Gradle modules, packages, endpoints, topics/queues, tables/schemas, configuration keys, secrets/trust, and deployment resources;
- upstream/downstream callers and compatibility requirements;
- Spring dependencies retained by this slice and shared dependencies that cannot yet be removed;
- baseline characterization cases and normalized behavior signatures;
- selected adapter and target implementation;
- rollout, rollback, coexistence, and data/protocol compatibility plan;
- target parity evidence and next eligible slice.

## Dependency order

Migrate leaf capabilities before shared platform modules when possible. Do not migrate a shared model, security library, transaction boundary, event schema, or configuration owner until every dependent slice has a compatible plan. In a multi-module build, compile the full reactor/build after each slice, not only the changed module.

## Completion criteria

Mark a slice `PASS` only when its baseline and Liberty target evidence match and the full build remains green. Mark the overall module `PARTIAL` while any selected slice remains Spring-backed. Never claim complete Spring removal until the analyzer, dependency graph, build files, source, tests, runtime configuration, and deployment artifacts show no unapproved Spring ownership.
