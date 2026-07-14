# Migration Report

Scope: staged migration of `/new`; `/legacy` remains Spring-owned.

| Module | Gate | State | Evidence | Validation | Resume point |
|---|---|---|---|---|---|
| code | Gate result: PARTIAL | PARTIAL | `NewResource` migrated; `LegacyController` retained | compile pending | Resume point: migrate `/legacy` after its client contract is approved |
