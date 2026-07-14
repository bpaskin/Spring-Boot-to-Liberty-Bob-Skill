# Module: Reactive, Spring Cloud, and Custom Runtime Adapter

Follow the [complex adapter contract](../references/complex-adapter-contract.md). Run when the inventory detects WebFlux, Reactor, R2DBC, Spring Cloud, Spring Integration without a messaging-only boundary, custom starters, auto-configuration, post-processors, custom scopes, or AOP/advisors.

## Default route

Prefer rehost-first or a staged exception. Do not mechanically replace a reactive pipeline with blocking Jakarta REST/JDBC or a Spring Cloud capability with a similarly named MicroProfile feature. Such changes can alter backpressure, cancellation, context, resource use, routing, discovery, refresh, retries, and transaction behavior.

## Capture by capability

- **Reactive:** publishers/subscribers, hot/cold behavior, concurrency, schedulers, backpressure, cancellation, context propagation, R2DBC transaction scope, streaming protocol, and resource limits.
- **Gateway/discovery:** route predicates/filters, header/path rewrites, load balancing, discovery registration, health, failover, TLS, rate limits, and dynamic refresh.
- **Config/Vault:** property precedence, refresh boundaries, encryption, lease renewal, failure behavior, and secret ownership.
- **Feign/RestClient/circuit breaker:** serialization, timeouts, retries, fallback, bulkhead, circuit state, DNS/discovery, and telemetry.
- **Custom runtime:** activation conditions, bean definition mutations, ordering, lifecycle, generated metadata, proxy/advisor behavior, and shutdown.

## Allowed routes

Choose one per capability: retain the compatible library with explicit CDI lifecycle; redesign behind a stable API; extract into a separately deployed service; retain the Spring slice; or rehost the whole application. Record load/performance acceptance criteria whenever execution style changes.

## Required characterization

Test streaming and cancellation, slow-consumer backpressure, downstream timeout, concurrency limits, route and discovery changes, config refresh, secret/backend outage, circuit/bulkhead transitions, extension activation/deactivation, and graceful shutdown.

## Completion criteria

Require behavior and load evidence. Compilation and endpoint happy paths cannot prove a reactive, routing, discovery, or custom-runtime rewrite.
