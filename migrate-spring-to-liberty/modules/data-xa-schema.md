# Module: Data, XA, and Schema Adapter

Follow the [complex adapter contract](../references/complex-adapter-contract.md) and load [production integration testing](../references/production-integration-testing.md). Run when the inventory detects external databases, multiple datasources, XA, Flyway/Liquibase, or non-default persistence behavior.

## Detect and capture

Inventory each datasource, driver/version, JNDI or configuration name, pool, validation query, isolation, timeout, credential owner, entity naming rule, schema/catalog, migration tool, transaction manager, enlisted resources, and recovery-log location. Trace repository queries and transaction boundaries rather than inferring behavior from properties alone.

## Select a route

- Use Liberty-managed datasources and Jakarta Transactions when the provider and XA semantics are supported and verified.
- Retain a compatible JDBC client or schema tool when Liberty does not replace its lifecycle or migration role.
- Use Jakarta Data only for repositories whose query, pagination, locking, and update semantics are proven compatible; otherwise use CDI plus `EntityManager` or a staged exception.
- Keep schema action `none` and Liberty table creation/removal disabled unless the user separately authorizes a named destructive test environment with a usable backup.

## Required characterization

Run representative reads/writes, query ordering/pagination, optimistic/pessimistic locking, validation failures, pool metrics, bad credentials, unavailable host, pool exhaustion, timeouts, reconnect, schema idempotence, checksum/lock failures, and restart behavior. For XA, force failure before and after each resource prepare/commit boundary and restart Liberty with an in-doubt transaction.

## Generate and migrate

Generate reviewable datasource, library, persistence, and variable scaffolding without embedding credentials. Verify driver visibility: server-managed resources require a Liberty library rather than a driver hidden inside the WAR. Preserve explicit table/column names where Spring naming strategies differ from the target provider.

## Diagnose schema and entity-enhancement regressions

- **Empty schema after startup:** do not assume a CDI bean's `@PostConstruct` method runs at application startup; normal bean instantiation can be lazy. Move required, non-destructive initialization to an `@Observes Startup` observer, make it idempotent and transaction-aware, and fail readiness when it cannot complete.
- **Expected table reported as missing:** resolve the repository's `dataStore` value before changing entity mappings. A Liberty `databaseStore` ID owns table policy and can apply its configured schema or `tablePrefix`, producing names that differ from an existing Spring-managed schema. For a pre-existing schema, bind directly to the reviewed datasource JNDI name (for example, `@Repository(dataStore = "jdbc/petclinic")`) or to an explicit persistence-unit reference when that is the selected contract. Capture generated SQL and compare the fully qualified table name with the live schema.
- **`IllegalAccessError` while traversing a lazy relationship:** inspect the provider stack trace and enhancement/weaving configuration. EclipseLink weaving may need to enhance entity classes or relationship accessors; `final` on the affected provider-managed class, field, or accessor can block that enhancement. Remove only the `final` modifier proven to block weaving, or select a supported access/fetch configuration—do not mechanically make the entire model mutable. Clean-rebuild the WAR and test both sides of every affected association inside the intended transaction boundary.

After each fix, rerun startup, schema inspection, representative repository operations, and lazy-association traversal. A successful deployment alone does not prove the persistence model is usable.

## Completion criteria

Require durable-state comparison and transaction-recovery evidence. A successful connection, compile, or single-resource rollback does not prove XA or schema parity.
