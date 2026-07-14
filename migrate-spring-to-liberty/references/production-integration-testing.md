# Production Integration Test Matrix

Load this reference when a migration uses a real database, identity provider, broker, telemetry backend, schema tool, XA transaction, or deployment platform. A compile or mocked client is not evidence for external-system parity.

## Evidence contract

For each integration, record the exact product/version, protocol, endpoint ownership, credentials/trust source, local test substitute, production difference, data cleanup policy, timeout, and unavailable-dependency behavior. Use disposable resources by default. Never point destructive tests at an unconfirmed shared environment.

| Integration | Positive evidence | Required failure evidence |
|---|---|---|
| PostgreSQL/JDBC | connect, query, write, pool metrics, schema/version | bad credentials, unavailable host, pool exhaustion, timeout, reconnect |
| Multiple datasources/XA | commit across all enlisted resources | failure between resource commits, rollback, heuristic/recovery visibility, restart recovery |
| Flyway/Liquibase | clean migration from supported baseline and idempotent restart | checksum mismatch, lock contention, incompatible schema, failed migration recovery |
| OIDC/JWT | valid issuer/audience/signature/claims/roles | missing, expired, bad signature, wrong issuer/audience, JWKS outage/rotation, insufficient role |
| Kafka/JMS/AMQP | publish/consume with schema, headers, ordering, acknowledgment | duplicate, poison/DLQ, broker loss, retry exhaustion, rebalance/failover, restart |
| Actuator/metrics/telemetry replacement | health groups, metric names/labels, trace/log correlation, exporter success | dependency-down readiness, exporter unavailable, sampling/backpressure, sensitive endpoint denial |
| Container/platform | immutable image, non-root run, probes, resources, config/secret binding | bad secret/config, failed readiness, termination drain, rollout rollback, denied network dependency |

## Test tiers

1. `STATIC_CONTRACT` — configuration and failure matrix are complete; no external service was started.
2. `DISPOSABLE_INTEGRATION` — tests use isolated containers or equivalent ephemeral services.
3. `LIBERTY_INTEGRATION` — the packaged application runs on Liberty against those services.
4. `PLATFORM_PARITY` — the target deployment platform demonstrates rollout, probes, secret/trust wiring, recovery, and observability.

Do not collapse unavailable infrastructure into a passing test. Record `BLOCKED` with the missing product, permission, credential, or network dependency and the command that would resume the test.

## Safety

- Pin container images by reviewed tag or digest and verify their provenance according to project policy.
- Randomize ports, topics, schemas, databases, realms, and consumer groups so concurrent tests cannot interfere.
- Keep credentials ephemeral and out of logs, command arguments, fixtures, and reports.
- Bound every wait and always stop resources in a finally/cleanup path.
- Capture server, broker/provider, schema-tool, and platform logs on failure.
- Assert externally observable behavior and durable side effects; do not pass solely on log text.
