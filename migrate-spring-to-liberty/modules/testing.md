# Module: Testing

Migrate test infrastructure from Spring Boot Test to MicroShed Testing (integration tests against a running Liberty container) and standard JUnit 5 (unit tests).

## What to do

- [ ] Replace `@SpringBootTest` integration tests with MicroShed Testing (`@MicroShedTest`)
- [ ] Replace `@MockBean` with Mockito or CDI `@Alternative` for unit tests
- [ ] Replace `TestRestTemplate` / MockMvc with MicroShed's injected REST clients or REST Assured
- [ ] Replace `@ActiveProfiles("test")` with Liberty server variables or MicroProfile Config overrides
- [ ] Replace `@LocalServerPort` with MicroShed's `@RESTClient` injection
- [ ] Move integration tests to `src/test/java` using the `IT` suffix (Failsafe convention)
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
import org.microshed.testing.liberty.LibertyServerContainerConfiguration;
import org.microshed.testing.SharedContainerConfiguration;
import org.testcontainers.junit.jupiter.Container;

public class AppDeploymentConfig implements SharedContainerConfiguration {

    @Container
    public static LibertyServerContainer server =
        new LibertyServerContainer()
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

Ensure these are in the build file (should already be added by the build module):

**Maven:**
```xml
<!-- MicroShed Testing with Liberty support -->
<dependency>
    <groupId>org.microshed</groupId>
    <artifactId>microshed-testing-liberty</artifactId>
    <version>0.9.2</version>
    <scope>test</scope>
</dependency>
<!-- Hibernate Validator — Bean Validation implementation required by MicroShed -->
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
testImplementation 'org.microshed:microshed-testing-liberty:0.9.2'
testImplementation 'org.hibernate.validator:hibernate-validator:9.0.1.Final'
testImplementation 'org.junit.jupiter:junit-jupiter:5.12.2'
testImplementation 'org.mockito:mockito-junit-jupiter:5.18.0'
testImplementation 'io.rest-assured:rest-assured:5.5.2'
testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
```

## Watch out

- **Docker required for MicroShed**: MicroShed Testing uses Testcontainers to start a real Liberty container. Docker (or Podman) must be running on the test machine. If Docker is unavailable, fall back to REST Assured against a Liberty instance started by `liberty:start` in a pre-integration-test phase.
- **Integration test naming**: Maven Failsafe runs tests ending in `IT` (e.g., `TodoResourceIT`). Unit tests (`TodoServiceTest`) run with Surefire. Keep these conventions for correct lifecycle separation.
- **Test port**: MicroShed uses a random port managed by Testcontainers. Never hardcode `localhost:9080` in integration tests — use the injected client or `server.getBaseURL()`.
- **No `@WebMvcTest` equivalent**: Use `@MicroShedTest` for all integration test types. For data-only tests, consider H2 in-memory with the `persistence-3.2` feature.
- **CDI `@Alternative` for mocking**: If you need to replace a CDI bean for a test, annotate a test implementation with `@Alternative` and `@Priority(1)` — no Spring-specific test annotations needed.
