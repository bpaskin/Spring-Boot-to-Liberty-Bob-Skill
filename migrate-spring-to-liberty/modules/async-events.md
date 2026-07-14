# Module: Async, Events, Transactions, and Retry

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md) and [complex adapter contract](../references/complex-adapter-contract.md). This module owns Spring execution semantics that cannot be preserved by replacing annotations in the general code module.

If the contract selects retain Spring and rehost, log `SKIP` and preserve Spring's executors, events, transaction interceptors, and retry infrastructure unchanged.

For a rewrite, inventory behavior before editing. If executor, event ordering, transaction, or retry semantics are unknown, mark the module `BLOCKED` or retain the complete Spring slice as a staged exception. A successful compile is not semantic parity.

## Gate inventory

Search source, configuration, build files, and tests for:

- `@Async`, `AsyncConfigurer`, `TaskExecutor`, `ThreadPoolTaskExecutor`, executor bean names, `CompletableFuture`, and uncaught-exception handlers
- `ApplicationEventPublisher`, `ApplicationEvent`, `@EventListener`, `@TransactionalEventListener`, listener conditions, ordering, and error handling
- Spring `@Transactional` propagation, isolation, timeout, read-only, rollback/no-rollback rules, and programmatic transaction templates
- Spring Retry `@Retryable`, `@Recover`, `RetryTemplate`, `RetryListener`, backoff, jitter, stateful retry, context attributes, and recovery callbacks
- queue bounds, rejection policy, concurrency limits, scheduling, virtual-thread settings, security/naming/request context, metrics, and shutdown/drain behavior

Add an **execution semantics matrix** to `migration-report.md`:

| Operation | Caller contract | Sync/async and executor | Context propagation | Transaction boundary | Failure/retry/recovery | Ordering/backpressure |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

## `@Async` and executor strategy

Use Jakarta Concurrency 3.1 (`concurrent-3.1`) and a container-managed `ManagedExecutorService` or `ManagedScheduledExecutorService`. Never create raw threads or an unmanaged `Executors` pool in a Jakarta EE application.

For each async method, preserve:

- the named/default executor selection and maximum concurrency
- queue capacity, submission timeout, rejection/caller-runs behavior, and overload response
- return type, cancellation, timeout, exception visibility, and uncaught-exception handling
- security, naming, classloader, transaction, and request-context expectations
- self-invocation behavior and whether execution was actually asynchronous in the baseline
- graceful shutdown, in-flight work, and duplicate-delivery/idempotency behavior

Inject the default managed executor or define a reviewed `managedExecutorService`/`concurrencyPolicy` with a stable JNDI name. Do not assume Spring pool sizes or queue policies match Liberty defaults. Use MicroProfile Context Propagation only when its API is intentionally selected; do not add it solely because `CompletionStage` is present.

## Application events

Map by delivery semantics:

| Spring behavior | Candidate Jakarta behavior | Required proof |
|---|---|---|
| synchronous `ApplicationEventPublisher` + `@EventListener` | CDI `Event<T>.fire()` + `@Observes` | observer selection, ordering, exception propagation, and caller transaction |
| asynchronous listener | CDI `fireAsync()` + `@ObservesAsync`, or explicit managed-executor dispatch | completion/failure handling, context, executor, and backpressure |
| `@TransactionalEventListener` | `@Observes(during = TransactionPhase...)` | exact before/after completion/success/failure phase |
| conditional listener or SpEL condition | explicit typed qualifier or tested predicate | do not copy the expression mechanically |

CDI asynchronous observers cannot be transactional observers. If Spring combines async delivery with transaction-phase behavior, split durable publication from asynchronous consumption (for example, an outbox or messaging design) or keep a staged exception. Preserve listener priority only after proving the chosen CDI priority/order behavior matches the baseline.

## Transaction semantics

Spring and Jakarta transaction annotations overlap but are not identical.

| Spring propagation | Jakarta `TxType` candidate |
|---|---|
| `REQUIRED` | `REQUIRED` |
| `REQUIRES_NEW` | `REQUIRES_NEW` |
| `MANDATORY` | `MANDATORY` |
| `SUPPORTS` | `SUPPORTS` |
| `NOT_SUPPORTED` | `NOT_SUPPORTED` |
| `NEVER` | `NEVER` |
| `NESTED` | no portable Jakarta annotation equivalent; redesign or stage |

Do not discard Spring isolation, timeout, read-only, rollback/no-rollback, transaction-manager selection, savepoint, or synchronization behavior. Jakarta `@Transactional` does not express all of these attributes. Preserve them through supported persistence/Liberty configuration or an explicit programmatic design, with rollback and concurrency tests. Verify checked-exception rollback rules rather than assuming the two frameworks agree.

## Retry and recovery

MicroProfile Fault Tolerance `@Retry` is a candidate only when attempts, delay, jitter, maximum duration, `retryOn`, and `abortOn` preserve the contract. Enable `mpFaultTolerance-4.1` only when selected.

Spring Retry listeners, stateful retry, retry-context mutation, keying, `@Recover` overload selection, and recovery callbacks have no automatic `@Retry` conversion. Implement an explicit interceptor/service or durable messaging pattern, or retain a staged Spring slice. Preserve idempotency, transaction-per-attempt behavior, metrics/audit hooks, cancellation, and final exception/recovery results.

## Required tests

- prove work runs off or on the caller thread as contracted and uses the intended executor
- exercise saturation, queue rejection/backpressure, cancellation, timeout, and async failure visibility
- verify propagated and deliberately cleared contexts
- verify synchronous, asynchronous, ordered, conditional, and transaction-phase event delivery
- verify commit, rollback, nested/`REQUIRES_NEW`, checked exception, timeout, and isolation-sensitive cases that apply
- verify retry count, delay bounds, retry/abort exception classes, transaction boundary per attempt, listener/audit hooks, and recovery result
- verify shutdown/drain and duplicate/idempotency behavior where work can outlive a request

Mark `PASS` only when the matrix is complete and applicable behavior tests pass. Otherwise record the exact staged dependency or blocker and do not claim complete Spring removal.

## Primary references

- [Open Liberty Jakarta Concurrency 3.1](https://www.openliberty.io/docs/latest/reference/feature/concurrent-3.1.html)
- [Open Liberty managed executor configuration](https://www.openliberty.io/docs/latest/reference/config/managedExecutorService.html)
- [Jakarta CDI 4.1 events](https://jakarta.ee/specifications/cdi/4.1/jakarta-cdi-spec-4.1)
- [Jakarta Transactions 2.0](https://jakarta.ee/specifications/transactions/2.0/)
- [MicroProfile Fault Tolerance 4.1](https://download.eclipse.org/microprofile/microprofile-fault-tolerance-4.1/microprofile-fault-tolerance-spec-4.1.html)
