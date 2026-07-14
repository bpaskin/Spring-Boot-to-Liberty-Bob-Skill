# Module: Identity and Observability Adapter

Follow the [complex adapter contract](../references/complex-adapter-contract.md), [security module](security.md), and [production integration testing](../references/production-integration-testing.md). Run when the inventory detects OIDC/OAuth2/JWT, Actuator, Micrometer, OpenTelemetry, custom health groups, or external telemetry backends.

## Detect and capture

Record issuer, audience, signature algorithms, JWKS behavior, claim/group mapping, authentication entry points, route policies, token propagation, session/cookie/logout rules, trust ownership, health groups, liveness/readiness semantics, metric names/labels, trace propagation, log correlation, sampling, exporter queues, and protected management endpoints.

Never copy credentials, private keys, bearer tokens, or trust material into the repository or migration report.

## Select a route

- Use `mpJwt-2.1` for verified bearer-JWT resource-server semantics.
- Use `openidConnectClient-1.0` only when an interactive OIDC client flow is required and its session/logout behavior is characterized.
- Keep an external identity proxy or retained library when Liberty/Jakarta mechanisms do not preserve the contract.
- Map each Actuator endpoint and observation to a selected MicroProfile/Liberty or external-platform replacement; do not treat similarly named metrics as equivalent without label and unit comparison.

## Required characterization

Test valid authentication, missing/expired/bad-signature tokens, wrong issuer and audience, insufficient roles, JWKS outage and rotation, clock skew, logout/session invalidation, protected health endpoints, dependency-down readiness, exporter outage, sampling/backpressure, and sensitive-data exclusion.

## Completion criteria

Require `401` versus `403` parity, fail-closed identity behavior, bounded exporter loss/backpressure, correlated telemetry evidence, and health behavior that matches the deployment contract.
