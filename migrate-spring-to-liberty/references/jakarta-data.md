# Spring Data to Jakarta Data 1.0

Load this reference only when the application contains Spring Data repository interfaces or repository-specific APIs.

## Choose the strategy before editing

Record one repository strategy in the migration contract:

| Strategy | Choose when | Open Liberty features |
|---|---|---|
| Jakarta Data 1.0 | CRUD plus supported automatic/annotated queries can preserve behavior, and repository interfaces are desirable | `data-1.0` + `persistence-3.2` for Jakarta Persistence entities |
| CDI + `EntityManager` | Specifications, custom fragments, provider extensions, explicit flush/lock behavior, or complex dynamic queries need direct control | `persistence-3.2` |
| Staged exception | The current migration scope cannot preserve repository behavior | Keep original code, add a precise migration TODO, and record the blocker |

`data-1.0` supplies Open Liberty's built-in relational Jakarta Data provider. `dataContainer-1.0` supplies only the Jakarta Data API; select it only when the application deliberately configures a separate provider. Do not enable both as alternatives. If multiple providers support the same entity model, disambiguate them explicitly; Open Liberty's built-in provider name is `Liberty`.

## Compatibility inventory

For every Spring Data interface, list its superinterfaces, declared methods, annotations, default methods, custom fragments, and callers. Classify each item before conversion:

| Spring Data usage | Jakarta Data path | Required verification |
|---|---|---|
| `CrudRepository` / basic `JpaRepository` CRUD | Jakarta Data `CrudRepository<T, K>` | `save`, `insert`, `update`, delete, collection return types, generated IDs, optimistic locking, and exceptions |
| `findBy…` method | Query by Method Name, `@Find`, or `@Query` | Keywords, nested properties, null parameters, case rules, limits, and ordering |
| `Page`, `Pageable`, `Sort`, `Slice` | `jakarta.data.page.Page`, `PageRequest`, `Order`, and `Sort` where semantics match | Page numbering, total-count behavior, cursor/offset choice, stable ordering, and response metadata |
| Spring `@Query` / `@Modifying` | Jakarta Data `@Query` or an explicit `EntityManager` method | Query language, named parameters, row count, transaction boundary, and cache/flush behavior |
| `JpaSpecificationExecutor`, Query by Example, projections, custom fragments | Usually CDI + `EntityManager`; use Jakarta Data only after a deliberate redesign | Generated SQL/results and every caller-visible contract |
| auditing, entity callbacks, locks, graphs, hints, stored procedures | Jakarta Persistence or provider-specific design | Principal/time source, transaction timing, lock modes, hints, and failure behavior |
| reactive repositories | No mechanical Jakarta Data 1.0 mapping | Preserve staged code or redesign the asynchronous boundary |

Identical simple names are not proof of compatibility. Spring Data and Jakarta Data both define `CrudRepository`, `Page`, and `Sort` concepts, but their APIs and contracts differ. Replace imports, inherited-method calls, and tests together.

## Repository conversion

```java
// Before
import org.springframework.data.jpa.repository.JpaRepository;

public interface TodoRepository extends JpaRepository<Todo, Long> {
    List<Todo> findByCompleted(boolean completed);
}
```

```java
// After
import jakarta.data.repository.CrudRepository;
import jakarta.data.repository.Repository;

@Repository(dataStore = "TodoStore")
public interface TodoRepository extends CrudRepository<Todo, Long> {
    List<Todo> findByCompleted(boolean completed);
}
```

Jakarta Data repository interfaces must be annotated with `jakarta.data.repository.Repository`. The example binds to a reviewed Liberty `databaseStore`; do not omit `dataStore` unless the contract explicitly chooses and configures `java:comp/DefaultDataSource`. Inject the generated repository with CDI:

```java
@Inject
TodoRepository todos;
```

For relational entities, retain Jakarta Persistence annotations and configuration. Add these Liberty features to the computed feature set:

```xml
<feature>data-1.0</feature>
<feature>persistence-3.2</feature>
```

## Bind the datastore without changing the schema

Choose and document one binding for each repository:

- **Persistence-unit reference** when the migration already uses `persistence.xml` or needs provider-specific Jakarta Persistence settings. Declare a `java:app`-scoped `@PersistenceUnit` reference on the repository and point `@Repository(dataStore = "...")` to that reference. Keep `jakarta.persistence.schema-generation.database.action=none`.
- **Liberty `databaseStore`** when server configuration should own the datasource and table policy. Point `dataStore` to the element ID and explicitly disable table creation and removal.
- **Datasource ID/JNDI name** only when direct datasource binding is intentional. Add `<data createTables="false" dropTables="false"/>`; otherwise Liberty's built-in provider attempts table creation by default.

Do not treat a `databaseStore` ID as an alias for its backing datasource. The `databaseStore` owns additional table policy, including configured schema and `tablePrefix`, so the repository can target generated names that do not match a pre-existing Spring schema. If the existing database contract owns a table such as `owners`, prefer the reviewed datasource JNDI name or a persistence-unit reference and preserve explicit entity table mappings. For example:

```java
@Repository(dataStore = "jdbc/petclinic")
public interface OwnerRepository extends CrudRepository<Owner, Integer> {
}
```

During verification, enable/capture provider SQL and compare the resolved catalog, schema, and table name with the live database. A symptom such as `WLPowners table not found` is evidence to inspect `databaseStore` schema/`tablePrefix` policy and the resolved `dataStore` binding before renaming the database table.

Non-destructive `databaseStore` example for the repository above:

```xml
<databaseStore id="TodoStore"
               dataSourceRef="TodoDataSource"
               createTables="false"
               dropTables="false"/>

<dataSource id="TodoDataSource">
    <!-- Reviewed driver and database-specific properties. Keep credentials external. -->
</dataSource>
```

If the application intentionally uses multiple Jakarta Data providers for the same entity annotation, set the provider too, for example `@Repository(provider = "Liberty", dataStore = "TodoStore")`.

## Migration procedure

1. Capture repository behavior with focused tests before changing the interface.
2. Convert the entity model and preserve explicit table/column names, IDs, versions, relationships, and converters.
3. Convert one repository and its callers at a time. Do not bulk-replace `CrudRepository` imports.
4. Map each inherited or declared method and resolve compile errors at call sites.
5. Preserve `jakarta.transaction.Transactional` boundaries at the service or repository operation that owns the unit of work.
6. Add `data-1.0` and the entity-model feature; bind every repository to the contract-selected datastore and keep schema/table creation and removal disabled by default.
7. Compile, run repository integration tests against the target database, and verify the resolved datastore, unchanged schema, pagination, ordering, generated IDs, optimistic locking, and exceptions.
8. Record unsupported behavior as a staged exception or switch that repository to CDI + `EntityManager`.

## Authoritative references

- [Jakarta Data 1.0 specification](https://jakarta.ee/specifications/data/1.0/jakarta-data-1.0)
- [Jakarta Data 1.0 API](https://jakarta.ee/specifications/data/1.0/apidocs/)
- [Open Liberty Jakarta Data 1.0 feature](https://openliberty.io/docs/latest/reference/feature/data-1.0.html)
- [Open Liberty built-in Jakarta Data provider](https://openliberty.io/docs/latest/built-in-jakarta-data-provider.html)
- [Open Liberty Jakarta Data store configuration](https://openliberty.io/docs/latest/data-store-configuration.html)
- [Open Liberty Jakarta Data Container 1.0 feature](https://openliberty.io/docs/latest/reference/feature/dataContainer-1.0.html)
