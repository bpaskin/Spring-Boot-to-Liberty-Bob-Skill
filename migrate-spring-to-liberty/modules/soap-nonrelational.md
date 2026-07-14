# Module: SOAP, RPC, Cache, and Non-Relational Adapter

Follow the [complex adapter contract](../references/complex-adapter-contract.md). Run when the inventory detects Spring Web Services, CXF, WSDL, SOAP interceptors, GraphQL/gRPC, Redis, MongoDB, Elasticsearch, Cassandra, Neo4j, JCache, or a custom cache/store integration.

## Detect and capture

Record protocol/schema versions, generated-code ownership, endpoint operations, SOAP headers/faults/interceptors, authentication and transport, serialization compatibility, client/server roles, store topology, consistency, TTL/eviction, transactions, atomic operations, indexes, query behavior, serialization, cluster/failover, connection pools, and shutdown.

## Select a route

- Use Jakarta XML Web Services only when WSDL, binding, handler, fault, and transport behavior can be preserved.
- Retain a compatible RPC or data client with explicit CDI/configuration/lifecycle wiring when Liberty does not supply an equivalent service.
- Use JCache only with a selected compatible provider; keep the `javax.cache` namespace and verify provider semantics.
- Redesign or stage capabilities whose consistency, query, streaming, or cluster behavior has no proven target.

Do not configure Redis or another non-relational store as a JDBC or JMS connection factory. Do not reduce a SOAP application to JAXB/XML binding.

## Required characterization

Test representative protocol messages or queries, schema/serialization compatibility, faults and invalid data, authentication failure, timeout, store outage, retry/reconnect, cache expiry/eviction, duplicate operations, failover, restart, and durable-state consistency.

## Completion criteria

Require wire-level or externally observable data evidence plus failure/recovery parity. Generated sources must remain reproducible from the authoritative schema.
