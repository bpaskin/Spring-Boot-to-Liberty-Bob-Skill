# Module: Non-Mechanical Stack Preflight

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md). Run this read-only gate immediately after the JDK check and before changing the build or source code for a rewrite.

If the contract selects retain Spring and rehost, record the detected stacks for runtime parity, mark this module `SKIP — rewrite not selected`, and preserve them.

## Inventory

Inspect dependencies, imports, annotations, configuration, generated metadata, and runtime behavior for:

| Stack | Representative evidence | Required route |
|---|---|---|
| Reactive web/data | WebFlux, Reactor `Mono`/`Flux`, functional routes, RSocket, R2DBC, reactive transactions | explicit reactive redesign or staged retention |
| Spring Cloud | Gateway, Config, OpenFeign, discovery, load balancing, Circuit Breaker, Stream, Function, Task, Vault, Kubernetes | capability-by-capability architecture contract |
| Spring Integration | channels, gateways, adapters, pollers, aggregators, splitters, routers, message stores | messaging module plus explicit flow topology |
| Messaging | Kafka, JMS, AMQP/RabbitMQ, Pulsar, Spring Cloud Stream | [messaging module](messaging.md) |
| Batch and scheduling | Spring Batch, Quartz, `@Scheduled`, task scheduling, clustered locks | [batch/scheduling module](batch-scheduling.md) |
| SOAP and RPC | Spring Web Services, CXF, WSDL, SOAP interceptors, GraphQL, gRPC | explicit protocol contract and verified implementation |
| Custom Spring runtime | custom starters, auto-configuration imports, `ImportSelector`, bean factory/registry post-processors, custom scopes, AOP/advisors | project-specific design or staged retention |
| Non-relational data/cache | Redis, MongoDB, Elasticsearch, Cassandra, Neo4j, custom cache managers | explicit client/provider, lifecycle, consistency, and failure contract |

Do not classify a stack from a dependency name alone. Trace its call sites, configuration, tests, and operational ownership. Conversely, do not miss programmatic usage merely because a starter is absent.

## Hard-block rules

For each detected stack, record one strategy:

1. `DEDICATED_MODULE` — this skill has an applicable semantic module and its contract is complete.
2. `RETAIN_LIBRARY` — remove Spring integration while retaining a compatible underlying library, with explicit CDI/configuration/lifecycle wiring.
3. `REDESIGN` — replace the capability with a documented Jakarta EE, MicroProfile, Liberty, or external-platform design.
4. `STAGED_EXCEPTION` — leave the Spring slice and its dependencies intact, name its boundary, and do not claim complete removal.
5. `REHOST` — preserve the whole Spring application on Liberty.

Mark this module `BLOCKED` when any detected stack lacks one of these strategies or when its baseline semantics are unknown. While blocked:

- do not remove its dependencies, configuration, generated metadata, or tests;
- do not run cleanup over its files;
- continue only modules proven independent of the blocked slice;
- do not report complete Spring removal.

Reactive behavior is never an annotation-only conversion. A switch from WebFlux/R2DBC to blocking Jakarta REST/JDBC changes concurrency, backpressure, cancellation, context, resource use, and transaction behavior. Require explicit authorization for that architecture change.

## Required contract evidence

Record, as applicable:

- public APIs, protocols, schemas, routes, status/error contracts, and compatibility/version constraints;
- concurrency, ordering, backpressure, cancellation, timeout, retry, duplicate, and idempotency behavior;
- connection pools, transactions, consistency, checkpoints, recovery, and shutdown behavior;
- service discovery, routing, load balancing, failover, secret/trust ownership, and network dependencies;
- generated configuration/metadata and custom extension lifecycle;
- positive, negative, overload, unavailable-dependency, restart, and recovery tests.

Mark `PASS` only when every detected stack has a confirmed strategy and its dependent module can proceed. Mark `SKIP` only after an evidence-backed scan finds none.

## Primary references

- [Spring Boot reactive web applications](https://docs.spring.io/spring-boot/reference/web/reactive.html)
- [Spring Boot R2DBC](https://docs.spring.io/spring-boot/reference/data/sql.html#data.sql.r2dbc)
- [Spring Boot messaging](https://docs.spring.io/spring-boot/reference/messaging/index.html)
- [Spring Boot task execution and scheduling](https://docs.spring.io/spring-boot/reference/features/task-execution-and-scheduling.html)
- [Open Liberty feature overview](https://openliberty.io/docs/latest/reference/feature/feature-overview.html)
