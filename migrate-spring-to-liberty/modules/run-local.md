# Module: Run Locally & Fix Log Errors

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md); record command, timeout, readiness evidence, logs, and cleanup result.

Start the migrated or rehosted application on Open Liberty locally, read the startup logs, and resolve any errors before declaring the work complete.

## What to do

- [ ] Start Liberty (dev mode recommended for iteration)
- [ ] Record command, readiness URL, log paths, and timeout before starting
- [ ] Confirm the server started successfully from the console output
- [ ] If the server fails to start or the app fails to deploy, locate the log files
- [ ] Triage each error in order: configuration → CDI wiring → JPA → JAX-RS → runtime
- [ ] Fix each error, recompile, and restart until the app is clean
- [ ] Verify the application responds to HTTP requests
- [ ] Stop the owned process gracefully and verify it exited on every outcome

## Time-bounded runtime lifecycle

Before starting, record the command, expected context root, readiness URL, log paths, and timeout in the migration ledger. Use 180 seconds unless the baseline or first-download conditions justify another explicit value. Confirm required ports are available and required external services are either running or documented as blockers.

For a Jakarta rewrite, use `liberty:dev` / `libertyDev` for the normal iterative path. For a retained-Spring rehost, use Maven's documented `liberty:run` goal or the verified foreground task exposed by the pinned Gradle plugin for the first parity run. Start it in a controllable foreground/PTY session, poll output in short intervals, and never wait silently past the recorded deadline.

Use the detected wrapper when present and the installed Maven/Gradle launcher otherwise; the commands below show wrapper form.

**Maven:**
```bash
# Rewrite
./mvnw liberty:dev

# Retain Spring and rehost
./mvnw liberty:run
```

**Gradle:**
```bash
# Rewrite
./gradlew libertyDev

# Retain Spring and rehost: inspect the pinned plugin's available foreground tasks,
# then record and use the documented task for that version.
./gradlew tasks --group liberty
```

Watch for this line in the console — it means the server is ready:

```
[INFO] [AUDIT   ] CWWKF0011I: The defaultServer server is ready to run a smarter planet.
```

Press `Enter` in dev-mode to run tests. Press `Ctrl+C` to stop.

Whether startup passes, fails, times out, or the task is interrupted, execute a cleanup step: send the foreground process `Ctrl+C`, wait for graceful shutdown, and verify the owned process exited. Never terminate an unverified process or force-kill merely to free a port.

### Non-interactive packaged alternative

When dev mode cannot be controlled reliably, build a self-contained runnable artifact and run it in the same time-bounded foreground lifecycle:

**Maven:**
```bash
./mvnw liberty:package -Dinclude=runnable
java -jar target/<artifactId>.jar
```

Derive the artifact name from the build output. Do not run dev mode and the packaged alternative simultaneously.

## Confirming Successful Startup

A successful startup produces this sequence in the console (order may vary):

```
[AUDIT] CWWKT0016I: Web application available (default_host): http://localhost:9080/<context-root>/
[AUDIT] CWWKZ0001I: Application <app-name> started in X.XXX seconds.
[AUDIT] CWWKF0011I: The defaultServer server is ready to run a smarter planet.
```

Quick smoke test after startup:
```bash
# If mpHealth feature is enabled
curl -s http://localhost:9080/health | python3 -m json.tool

# Basic endpoint test
curl -v http://localhost:9080/<context-root>/api/<resource>
```

## Log File Locations

When the console output is not enough, read the log files written by Liberty.

| Log | Path (relative to project root) | Contains |
|---|---|---|
| Console output | printed to terminal | All AUDIT/ERROR messages during startup |
| `messages.log` | `target/liberty/wlp/usr/servers/defaultServer/logs/messages.log` (Maven) | All messages — primary diagnostic file |
| `trace.log` | same directory, `trace.log` | Detailed trace output (only if trace spec is enabled) |
| `ffdc/` | same directory, `ffdc/` | First-failure data capture — full stack traces for unexpected errors |

For Gradle, replace `target/liberty` with `build/wlp`.

Read the last 100 lines of messages.log:
```bash
# Maven
tail -100 target/liberty/wlp/usr/servers/defaultServer/logs/messages.log

# Gradle
tail -100 build/wlp/usr/servers/defaultServer/logs/messages.log
```

Read FFDC stack traces (most recent first):
```bash
# Maven
ls -lt target/liberty/wlp/usr/servers/defaultServer/logs/ffdc/ | head -5
cat target/liberty/wlp/usr/servers/defaultServer/logs/ffdc/<most-recent>.txt
```

## Common Errors and Fixes

Work through errors in this order — configuration errors block CDI, CDI errors block JPA, etc.

---

### 1. Feature not found / feature conflict

**Symptom:**
```
CWWKF0001E: A feature named xxx-Y.Z does not exist.
CWWKF0033E: The feature xxx-Y.Z conflicts with the currently installed feature yyy-A.B.
```

**Fix:**
- Verify the feature name in [`server.xml`](../modules/build.md) — check exact name and version against the [Open Liberty feature list](https://openliberty.io/docs/latest/reference/feature/feature-overview.html).
- Remove conflicting features — `jakartaee-11.0` already includes `cdi-4.1`, `restfulWS-4.0`, `persistence-3.2`, etc. Do not list both the umbrella and its sub-features.
- Ensure you are running Open Liberty (not WebSphere Application Server) for `jakartaee-11.0` and `microProfile-7.0`.

---

### 2. Application artifact not found

**Symptom:**
```
CWWKZ0014W: The application <name> could not be started as it could not be found at location ...
```

**Fix:**
- For a rehost, verify `<springBootApplication location="..."/>` names the actual executable Spring Boot JAR/WAR and that the matching `springBoot-3.0` or `springBoot-4.0` feature is enabled. Do not replace it with `<webApplication>`.
- Use `./mvnw liberty:dev` / `./gradlew libertyDev` — this builds and deploys automatically; no separate package step is needed.
- Verify `<webApplication location="..."/>` in `server.xml` uses `${server.config.dir}/apps/<artifactId>.war`.
- The `<finalName>` in `pom.xml` (or `archiveFileName` in Gradle) must match the WAR location in `server.xml`.

---

### 3. CDI deployment failure — unsatisfied/ambiguous dependency

**Symptom:**
```
CWOWB0000E: CDI deployment failure: WELD-001408: Unsatisfied dependencies for type X with qualifiers @Default
CWOWB0000E: CDI deployment failure: WELD-001409: Ambiguous dependencies for type X
```

**Fix for unsatisfied dependency:**
- The class being injected is not a CDI bean — ensure it has a scope annotation (`@ApplicationScoped`, `@RequestScoped`, etc.)
- Check that `beans.xml` is present. Create `src/main/webapp/WEB-INF/beans.xml` (see [cleanup.md](cleanup.md)):
  ```xml
  <?xml version="1.0" encoding="UTF-8"?>
  <beans xmlns="https://jakarta.ee/xml/ns/jakartaee"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="https://jakarta.ee/xml/ns/jakartaee
                             https://jakarta.ee/xml/ns/jakartaee/beans_4_0.xsd"
         version="4.0"
         bean-discovery-mode="annotated">
  </beans>
  ```
- If the bean is in a library JAR that has no `beans.xml`, CDI annotated-discovery mode only picks up beans with a scope annotation — add the annotation or switch to `bean-discovery-mode="all"` for debugging.

**Fix for ambiguous dependency:**
- Two beans implement the same type and CDI cannot choose. Annotate the preferred implementation with `@Default` and the alternative with `@Alternative` + `@Priority(1)`, or use a CDI `@Qualifier`.

---

### 4. JPA / DataSource errors

**Symptom:**
```
DSRA0010E: SQL State = 08001, Error Code = 0, Message: ... (connection refused / database not found)
CWWJP0014E: Persistence unit "defaultPU" could not be configured.
```

**Fix for DataSource connection error:**
- Verify the database is running locally before starting Liberty.
- Check `server.xml` `<dataSource>` coordinates: `url`, `user`, `password` must match your local database.
- Ensure the JDBC driver JAR is on Liberty's classpath: either bundled in the WAR (`<scope>runtime</scope>` in Maven) or in a `<library>` referenced from `<dataSource>`.
- For local development without a database, use H2 in-memory and add to `server.xml`:
  ```xml
  <dataSource id="DefaultDataSource" jndiName="jdbc/myapp">
      <jdbcDriver libraryRef="H2Lib"/>
      <properties.derby.embedded databaseName="memory:myapp" createDatabase="create"/>
  </dataSource>
  ```

**Fix for persistence unit configuration error:**
- Verify `persistence.xml` exists at `src/main/resources/META-INF/persistence.xml`.
- Ensure `transaction-type="JTA"` is set — Liberty manages JTA transactions; `RESOURCE_LOCAL` does not work with `@PersistenceContext` injection.
- Add the `persistence-3.2` feature to `server.xml` (or use the `jakartaee-11.0` umbrella).

**Schema is still empty after a clean startup:**
- Find the code expected to initialize or seed it. An ordinary CDI bean can be created lazily, so its `@PostConstruct` method is not a reliable application-start event.
- Move required startup work to an `@Observes Startup` observer, make the operation idempotent and transaction-aware, and surface failures through deployment/readiness rather than continuing with an empty schema.
- Recheck that destructive schema creation was actually authorized; do not enable automatic creation merely to hide a missing initializer.

**Expected table is reported as not found:**
- Resolve `@Repository(dataStore = "...")` to its actual datasource, persistence-unit reference, or Liberty `databaseStore`.
- A `databaseStore` ID is not merely its datasource alias; its schema and `tablePrefix` policy can produce a name such as `WLPowners` instead of the existing `owners` table.
- For an existing schema, bind to the reviewed datasource JNDI name (for example, `@Repository(dataStore = "jdbc/<name>")`) or the explicit persistence-unit reference selected by the contract. Capture SQL and compare catalog/schema/table names before editing the database.

**`IllegalAccessError` names a lazy entity relationship:**
- Inspect the complete provider stack trace and EclipseLink weaving/enhancement configuration.
- If the affected entity class, relationship field, or accessor is `final`, remove only the modifier proven to prevent weaving or choose a supported access/fetch configuration. Do not remove `final` mechanically from unrelated domain code.
- Clean-rebuild and test traversal of both sides of the relationship inside the intended transaction; also verify the expected behavior outside it.

---

### 5. JAX-RS application not reachable (404)

**Symptom:**
```
HTTP 404 Not Found on http://localhost:9080/<context-root>/api/...
```

**Fix:**
- Confirm `contextRoot` in `server.xml` `<webApplication>` matches the URL you are calling.
- Confirm the JAX-RS `Application` class exists and has the contract-selected path, such as `@ApplicationPath("/api")`.
- Inventory Servlet URL patterns too. `@ApplicationPath("/")` overlaps `@WebServlet("/")`, and the front Servlet can consume the JAX-RS request. Move JAX-RS to a non-overlapping path such as `/api` and update clients/tests, or narrow the Servlet mapping.
- Look for `CWWKZ0001I: Application ... started` in the logs — if missing, the app failed to deploy (look for earlier errors).
- Check that the resource class has `@Path` and the CDI scope annotation (`@ApplicationScoped` or `@RequestScoped`).
- Verify the resource method has the correct HTTP method annotation (`@GET`, `@POST`, etc.) and `@Produces`/`@Consumes` annotations.

---

### 6. ClassNotFoundException / NoClassDefFoundError

**Symptom:**
```
java.lang.ClassNotFoundException: com.example.SomeClass
java.lang.NoClassDefFoundError: jakarta/...
```

**Fix:**
- A `jakarta.*` class is missing → ensure `jakarta.platform:jakarta.jakartaee-api` is `provided` scope and the `jakartaee-11.0` feature is in `server.xml`.
- A third-party class is missing → ensure the dependency is `compile` or `runtime` scope (not `provided`) so it is bundled in the WAR.
- Check the WAR contents: `jar tf target/<artifactId>.war` and verify `WEB-INF/lib/` contains the expected JARs.

---

### 7. javax.* vs jakarta.* import errors at runtime

**Symptom:**
```
ClassCastException: class org.hibernate.SessionImpl cannot be cast to class javax.persistence.EntityManager
```

**Fix:**
- A library on the classpath still uses `javax.*` APIs — this causes split-package conflicts with Liberty's `jakarta.*` implementation.
- Run `grep -rn "import javax\." src/` and replace all `javax.persistence`, `javax.inject`, `javax.annotation`, `javax.transaction`, `javax.validation`, `javax.servlet` with `jakarta.*` equivalents.
- Inspect transitive `javax.*` dependencies and remove only incompatible legacy Java/Jakarta EE APIs. Preserve Java SE and intentional third-party APIs such as JCache; verify each dependency rather than filtering by namespace alone.

---

### 8. Port already in use

**Symptom:**
```
CWWKO0221E: TCP Channel defaultHttpEndpoint initialization did not succeed. The port 9080 may already be in use.
```

**Fix:**
```bash
# Find what is using the port
lsof -i :9080

# After identifying the owner and receiving confirmation, stop it gracefully
kill <PID>
```

Or change the Liberty port in `server.xml`:
```xml
<httpEndpoint id="defaultHttpEndpoint" host="*" httpPort="9081" httpsPort="9444"/>
```

Show the process identity and owning user before proposing termination. Ask for confirmation, then stop only the confirmed process gracefully. Never force-kill an unknown process merely to free a port.

---

### 9. Serialization / JSON-B errors

**Symptom:**
```
jakarta.json.bind.JsonbException: Unable to serialize property 'xyz' from class ...
RESTEASY003175: Could not find writer for content-type application/json
```

**Fix:**
- The entity class must have a no-arg constructor (JSON-B requirement).
- Cyclic references (e.g., bidirectional JPA relationships) cause infinite serialization. Break the cycle with `@JsonbTransient` on the back-reference field.
- If the app was relying on Jackson annotations (`@JsonProperty`, `@JsonIgnore`), either:
  - Replace them with JSON-B equivalents (`@JsonbProperty`, `@JsonbTransient`)
  - Or add Jackson JAX-RS provider: `com.fasterxml.jackson.jakarta.rs:jackson-jakarta-rs-json-provider` to the WAR and register a `ContextResolver<ObjectMapper>`.

---

### 10. Core Thymeleaf field-expression errors

**Symptom:**
```
TemplateProcessingException while evaluating #fields.hasErrors(...)
```

**Fix:**
- `#fields` and `th:errors` depend on the Thymeleaf-Spring integration and are unavailable after moving to core Thymeleaf.
- Make the controller always provide an explicit `errors` map, including an empty map for the initial GET.
- Replace a dynamic field check with `${errors.containsKey(name)}` and render its escaped message with `th:text="${errors.get(name)}"`.
- Test valid input, each representative field error, global errors, redisplayed values, escaping, and accessibility attributes before removing the Spring dialect.

---

## Enabling Trace Logging for Deeper Diagnostics

If errors are unclear, enable detailed tracing in `server.xml` for specific packages:

```xml
<logging traceSpecification="com.example.*=all:CDI=debug:WAS.j2c=debug"
         traceFileName="trace.log"
         maxFileSize="20"
         maxFiles="5"/>
```

Common trace specifications:
| Component | Trace spec |
|---|---|
| CDI (Weld) | `CDI=debug` |
| JPA (Hibernate) | `org.hibernate.*=debug` |
| JAX-RS | `com.ibm.ws.jaxrs.*=debug` |
| DataSource / JDBC | `WAS.j2c=debug` |
| Liberty server config | `config=debug` |

Remove or reduce trace specifications once the issue is resolved — trace logging can significantly slow startup.

## Watch out

- **Prefer dev mode for iteration**: use the packaged foreground alternative when dev mode cannot be controlled or reproduced. In both paths, enforce the recorded timeout and cleanup step.
- **FFDC files**: Liberty creates an FFDC file for every unexpected exception. These contain the full stack trace and are the primary debugging artifact for errors that produce no console message.
- **Liberty downloads on first run**: The first `liberty:dev` / `libertyDev` will download Open Liberty from Maven Central. This requires internet access and may take a minute. Subsequent runs use the cached download.
- **Feature installation on first run**: Liberty installs declared features on first startup. Watch for `CWWKF0012I: The server installed the following features` — this is normal.
- **Context root default**: If you see a 404 at `/`, the context root is `/<artifactId>` by default. Add `contextRoot="/"` to `<webApplication/>` in `server.xml` or use `liberty.var.app.context.root=/` in `pom.xml` properties.
