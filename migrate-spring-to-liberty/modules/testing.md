# Module: Testing

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md); preserve baseline test evidence and avoid duplicating test infrastructure on rerun.

Preserve every existing test and add only the integration coverage needed to verify behavior on Liberty. Treat an application with no tests as an explicit coverage risk rather than silently declaring the module complete.

When the security gate runs, preserve and execute the authorization, authentication, CSRF, CORS, session, and logout matrix defined by [the security module](security.md). This module supplies the test harness; it must not narrow or reinterpret that security contract.

Apply the contract scope before changing tests:

- **Complete or staged rewrite**: migrate Spring-specific test infrastructure only for the rewritten slice, using the guidance below.
- **Retain Spring and rehost**: keep `@SpringBootTest`, MockMvc, `TestRestTemplate`, Spring test profiles, and Spring test dependencies unchanged. Run them as the baseline suite, then add only a Liberty-hosted smoke/security test when existing tests do not exercise the deployed artifact. Never replace Spring tests with MicroShed merely because the host changes.

## Rehost checklist

- [ ] Keep the Spring test dependencies, annotations, profiles, and runners unchanged
- [ ] Run the original test command and compare counts/failures with the baseline
- [ ] Add a Liberty-hosted smoke/security test only when existing tests do not exercise the deployed artifact
- [ ] Verify both successful and denied/unauthenticated routes that can change across web containers
- [ ] Do not claim framework migration coverage; report that Spring was retained

## Rewrite checklist

- [ ] Replace `@SpringBootTest` integration tests with MicroShed Testing (`@MicroShedTest`)
- [ ] Replace `@MockBean` with Mockito or CDI `@Alternative` for unit tests
- [ ] Replace `TestRestTemplate` / MockMvc with MicroShed's injected REST clients or REST Assured
- [ ] Replace `@ActiveProfiles("test")` with Liberty server variables or MicroProfile Config overrides
- [ ] Replace `@LocalServerPort` with MicroShed's `@RESTClient` injection
- [ ] Move integration tests to `src/test/java` using the `IT` suffix (Failsafe convention)
- [ ] Preserve and run plain JUnit tests even when they contain no Spring annotations
- [ ] Compare test counts and failures with the baseline; distinguish pre-existing failures from regressions
- [ ] If no tests exist, record `SKIP` plus a coverage gap and propose minimal smoke/security tests
- [ ] Run tests: `./mvnw verify` (Maven) or `./gradlew test integrationTest` (Gradle)

## Key Conversions

### Integration test (full container)

```java
// BEFORE: Spring Boot Test
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
public class TodoControllerTest {
    @Autowired TestRestTemplate restTemplate;
    @MockBean TodoService todoService;

    @Test
    void shouldListTodos() {
        when(todoService.findAll()).thenReturn(List.of(new Todo("Test")));
        ResponseEntity<String> response = restTemplate.getForEntity("/api/todos", String.class);
        assertEquals(200, response.getStatusCode().value());
    }
}

// AFTER: MicroShed Testing (starts Liberty + deploys WAR automatically)
import org.microshed.testing.jaxrs.RESTClient;
import org.microshed.testing.jupiter.MicroShedTest;
import org.microshed.testing.SharedContainerConfig;

@MicroShedTest
@SharedContainerConfig(AppDeploymentConfig.class)
public class TodoResourceIT {

    @RESTClient
    static TodoResourceClient todoClient;   // JAX-RS typed client generated from the resource interface

    @Test
    void shouldListTodos() {
        List<Todo> todos = todoClient.list();
        assertNotNull(todos);
    }
}
```

### AppDeploymentConfig

Create a shared container configuration class (once per project):

```java
import org.microshed.testing.SharedContainerConfiguration;
import org.microshed.testing.testcontainers.ApplicationContainer;
import org.testcontainers.junit.jupiter.Container;

public class AppDeploymentConfig implements SharedContainerConfiguration {

    @Container
    public static ApplicationContainer server =
        new ApplicationContainer()
            .withAppContextRoot("/")
            .withReadinessPath("/health/ready"); // requires mpHealth feature
}
```

### Unit test (no container)

For pure unit tests of business logic, use JUnit 5 + Mockito directly. No Spring or MicroShed needed:

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class TodoServiceTest {

    @Mock
    TodoRepository repository;

    @InjectMocks
    TodoService todoService;

    @Test
    void findAll_returnsAll() {
        when(repository.findAll()).thenReturn(List.of(new Todo("Test")));
        List<Todo> result = todoService.findAll();
        assertEquals(1, result.size());
    }
}
```

## Dependencies

Resolve and record a MicroShed release that supports the Jakarta namespace used by the migrated application. MicroShed 0.9.2 is a `javax`-namespace baseline; do not copy that version blindly into a Jakarta EE 11 project. Pin the verified version as `MICROSHED_VERSION` and use the same value for Maven and Gradle.

Ensure these are in the build file when the corresponding test pattern is used:

**Maven:**
```xml
<!-- MicroShed Testing with Liberty support -->
<dependency>
    <groupId>org.microshed</groupId>
    <artifactId>microshed-testing-liberty</artifactId>
    <version>{MICROSHED_VERSION}</version>
    <scope>test</scope>
</dependency>
<!-- Add a validation implementation only when tests execute validation outside Liberty. -->
<dependency>
    <groupId>org.hibernate.validator</groupId>
    <artifactId>hibernate-validator</artifactId>
    <version>9.0.1.Final</version>
    <scope>test</scope>
</dependency>
<!-- JUnit 5 -->
<dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <version>5.12.2</version>
    <scope>test</scope>
</dependency>
<!-- Mockito for unit tests -->
<dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-junit-jupiter</artifactId>
    <version>5.18.0</version>
    <scope>test</scope>
</dependency>
<!-- REST Assured (optional — alternative to MicroShed RESTClient) -->
<dependency>
    <groupId>io.rest-assured</groupId>
    <artifactId>rest-assured</artifactId>
    <version>5.5.2</version>
    <scope>test</scope>
</dependency>
```

**Gradle:**
```groovy
testImplementation 'org.microshed:microshed-testing-liberty:{MICROSHED_VERSION}'
testImplementation 'org.hibernate.validator:hibernate-validator:9.0.1.Final'
testImplementation 'org.junit.jupiter:junit-jupiter:5.12.2'
testImplementation 'org.mockito:mockito-junit-jupiter:5.18.0'
testImplementation 'io.rest-assured:rest-assured:5.5.2'
testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
```

## Watch out

- **Container runtime required for MicroShed**: MicroShed Testing uses Testcontainers to start a Liberty container. Docker or a correctly configured compatible runtime must be available. If it is unavailable, report the blocked integration tests instead of silently replacing them with a weaker test.
- **Integration test naming**: Maven Failsafe runs tests ending in `IT` (e.g., `TodoResourceIT`). Unit tests (`TodoServiceTest`) run with Surefire. Keep these conventions for correct lifecycle separation.
- **Test port**: MicroShed uses a random port managed by Testcontainers. Never hardcode `localhost:9080` in integration tests — use the injected client or `server.getBaseURL()`.
- **No `@WebMvcTest` equivalent**: Use `@MicroShedTest` for all integration test types. For data-only tests, consider H2 in-memory with the `persistence-3.2` feature.
- **CDI `@Alternative` for mocking**: If you need to replace a CDI bean for a test, annotate a test implementation with `@Alternative` and `@Priority(1)` — no Spring-specific test annotations needed.
