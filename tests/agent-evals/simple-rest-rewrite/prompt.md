Use the `$migrate-spring-to-liberty` skill at `{skill_path}` to migrate the application in `{workspace}`.

The user has already confirmed this complete migration contract: remove Spring entirely; target JDK 21; stay in the current isolated evaluation workspace; use REST only; no datasource, security, async/events, messaging, batch, frontend views, external services, or deployment deliverables; preserve the `/api/greeting` status, JSON shape, and plain JUnit behavior; use Maven and Open Liberty; do not commit or push.

Implement the migration, create `migration-report.md`, run the applicable build/tests and a time-bounded Liberty smoke test when possible, cleanly stop owned processes, and leave the finished files in the evaluation workspace. Do not ask questions already answered by the contract.
