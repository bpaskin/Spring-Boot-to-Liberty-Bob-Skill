# Module: Batch and Scheduling

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md). Run for rewrite scopes that contain Spring Batch, Quartz, `@Scheduled`, `TaskScheduler`, cron/fixed-delay work, or mixed migrated jobs.

If the contract selects rehost, mark `SKIP` and preserve Spring's scheduler/job repository and configuration.

## Inventory semantics before selecting an API

For each job or trigger, record:

- trigger type, expression/time zone, misfire policy, overlap/concurrency rule, persistent/clustered ownership, and manual launch API;
- job identity/parameters, restartability, incrementer behavior, instance/execution uniqueness, checkpoints, step transitions, listeners, skips, retries, and limits;
- reader/processor/writer chunk size, transaction boundary, partitioning, remote steps, tasklets, and execution context data;
- job repository schema/retention, lock ownership, abandoned/stopped execution recovery, and operator endpoints;
- external dependencies, credentials, idempotency, duplicate side effects, shutdown, and observability.

Spring cron, Enterprise Beans calendar timers, Quartz, and container-managed scheduled executors are not expression-compatible. Never copy a cron string without proving every field, time zone, daylight-saving transition, and misfire behavior.

## Select a strategy

| Spring behavior | Candidate | Use only when |
|---|---|---|
| Spring Batch job/step/chunk | Jakarta Batch 2.1 (`batch-2.1`) | job XML/code can preserve restart, checkpoint, transition, partition, listener, and repository behavior |
| Quartz job | retain Quartz | durable/clustered triggers, calendars, misfire instructions, or operational tooling are required |
| simple cron schedule | Enterprise Beans `@Schedule` with `enterpriseBeansLite-4.0` | calendar expression and nonpersistent/persistent timer behavior are proven equivalent |
| fixed-rate/delay programmatic work | `ManagedScheduledExecutorService` with `concurrent-3.1` | lifecycle, overlap, context, rejection, and shutdown are explicitly managed |
| platform scheduler | external Kubernetes/OpenShift/enterprise scheduler | singleton ownership, retries, deadlines, and invocation authentication are defined |

Do not use an in-memory timer for a job that was clustered, persistent, or restartable. Do not enable automatic batch or scheduler schema creation in a durable environment without the shared destructive-action approval.

## Jakarta Batch requirements

When selecting Jakarta Batch:

1. Enable `batch-2.1` and configure a reviewed `batchPersistence`/datasource when durable job state is required.
2. Map job parameters, instance identity, restart behavior, step transitions, chunk checkpoints, skips/retries, partitioning, and listeners explicitly.
3. Preserve transaction boundaries and ensure readers/writers are restart-safe and idempotent.
4. Define how operations start, stop, abandon, restart, and inspect jobs; do not assume Spring Batch Actuator/custom endpoints still exist.
5. Migrate repository schema through the approved schema tool and test upgrade/rollback separately.

## Required tests

Test applicable cases with a real scheduler/job repository:

- normal launch and completion with exact job parameters;
- duplicate launch and concurrent launch;
- failure before and after a checkpoint, then restart;
- skip/retry/listener/transition limits and terminal status;
- transaction rollback with no partial duplicate side effects;
- crash or server restart while running;
- cron/fixed-rate timing, time zone, daylight-saving boundary, overlap, and misfire;
- clustered singleton/partition ownership when promised;
- stop, abandon, shutdown, and operational status visibility;
- unavailable datasource or downstream service and subsequent recovery.

Mark `PASS` only when restart and failure behavior match the contract. A successful one-shot execution is insufficient for a restartable batch job.

## Primary references

- [Open Liberty Jakarta Batch 2.1](https://openliberty.io/docs/latest/reference/feature/batch-2.1.html)
- [Open Liberty Jakarta Enterprise Beans Lite 4.0](https://openliberty.io/docs/latest/reference/feature/enterpriseBeansLite-4.0.html)
- [Open Liberty Jakarta Concurrency 3.1](https://openliberty.io/docs/latest/reference/feature/concurrent-3.1.html)
- [Spring Boot Batch](https://docs.spring.io/spring-boot/reference/io/spring-batch.html)
- [Spring Boot Quartz](https://docs.spring.io/spring-boot/reference/io/quartz.html)
