# Module: Messaging and Integration Flows

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md) and [complex adapter contract](../references/complex-adapter-contract.md). Run only for a rewrite scope with Spring Kafka, JMS, AMQP/RabbitMQ, Pulsar, Spring Cloud Stream, or Spring Integration messaging behavior.

If the contract selects rehost, mark `SKIP` and preserve Spring messaging configuration and tests.

## Inventory the behavioral topology

For every producer, consumer, channel, and integration flow, record:

- broker/provider, protocol, destinations/topics, partitions, consumer groups, subscriptions, routing keys, and selectors;
- payload format, schema/version compatibility, headers, keys, converters, serializers, and deserializers;
- delivery and acknowledgment mode, offset/commit boundary, ordering scope, concurrency, prefetch/batch size, and backpressure;
- retry owner, redelivery delay, poison-message policy, dead-letter destination, recovery handler, and duplicate/idempotency rules;
- local/JTA/XA transaction boundary and whether database work and message acknowledgment are atomic;
- security protocol, credentials, TLS/trust, ACLs, and secret ownership;
- startup dependency, readiness behavior, reconnect/failover, shutdown/drain, and observability;
- Spring Integration topology: pollers, gateways, routers, splitters, aggregators, resequencers, adapters, and persistent message stores.

Mark the module `BLOCKED` rather than guessing when acknowledgment, transaction, ordering, retry, schema, or failure ownership is unknown.

## Select one implementation per flow

| Existing flow | Candidate | Boundary |
|---|---|---|
| Spring Kafka listener/template | MicroProfile Reactive Messaging 3.0 with Liberty Kafka connector, or retained Kafka client | Liberty provides a Kafka connector; preserve group/client IDs, ack/commit, serializers, rebalance, and retry behavior |
| Spring JMS | Jakarta Messaging 3.1 plus a verified Jakarta Connectors 2.1 resource adapter/provider | `messaging-3.1` supplies APIs/configuration, not a broker; configure exact connection factory, destination, activation specification, and recovery |
| Spring AMQP/RabbitMQ | retained RabbitMQ Java client, or a separately verified Reactive Messaging connector | Liberty does not make RabbitMQ a Kafka-compatible connector; never add `mpReactiveMessaging-3.0` without an actual connector |
| Spring Cloud Stream | explicit Reactive Messaging channels or retained binder | inventory binder-specific partitioning, headers, error channels, retries, and DLQ semantics |
| Spring Integration | explicit CDI/service flow, Reactive Messaging, Jakarta Messaging, scheduler, or retained library | translate the topology, not just endpoint annotations |

Do not mix two consumers for the same destination during cutover unless the contract defines duplicate handling. Prefer a parallel shadow consumer only when it cannot acknowledge or mutate production data.

## Kafka conversion requirements

When selecting the Liberty Kafka connector:

1. Enable `mpReactiveMessaging-3.0` and include a compatible `org.apache.kafka:kafka-clients` dependency.
2. Configure `connector=liberty-kafka`, bootstrap servers, topic, group/client identity, serializers, and deserializers through MicroProfile Config.
3. Map the Spring acknowledgment mode to an explicit Reactive Messaging acknowledgment/commit design. Do not rely on defaults.
4. Preserve record/batch listener shape, partition ordering, retry/DLQ ownership, tombstone handling, headers, and tracing propagation.
5. Test rebalance, duplicate delivery, poison records, broker loss, reconnect, and shutdown drain.

## JMS conversion requirements

Enable `messaging-3.1` only with a provider contract. Configure the provider's resource adapter and the exact Liberty `jmsConnectionFactory`, destination, and activation specification. Add `mdb-4.0` only if the selected design uses message-driven beans.

Prove transacted-session/JTA behavior, redelivery count, selector/durable-subscription identity, expiration/priority, recovery after server restart, and provider failover. XA requires a recovery-capable resource adapter and must be tested with an actual failure between enlisted resources.

## Required tests

At minimum, test:

- successful publish/consume with payload, headers, key, and schema preserved;
- duplicate delivery and idempotent side effects;
- poison message and dead-letter/recovery outcome;
- retry/redelivery count and delay bounds;
- ordering at the promised scope under concurrent load;
- broker unavailable at startup and during processing;
- authentication/TLS failure without secret leakage;
- transaction commit and rollback, including crash/restart recovery when applicable;
- consumer rebalance or provider failover;
- graceful shutdown with in-flight work drained or deliberately abandoned.

Mark `PASS` only when the selected broker-backed tests and required negative cases pass. A compile with mocked clients is not messaging parity.

## Primary references

- [Open Liberty MicroProfile Reactive Messaging 3.0](https://openliberty.io/docs/latest/reference/feature/mpReactiveMessaging-3.0.html)
- [Open Liberty Kafka connector](https://openliberty.io/docs/latest/liberty-kafka-connector.html)
- [Liberty Kafka connector acknowledgment properties](https://openliberty.io/docs/latest/liberty-kafka-connector-channel-properties.html)
- [Open Liberty Jakarta Messaging 3.1](https://openliberty.io/docs/latest/reference/feature/messaging-3.1.html)
- [Open Liberty Message-Driven Beans 4.0](https://openliberty.io/docs/latest/reference/feature/mdb-4.0.html)
