# Module: Code

Migrate all Java source code from Spring patterns to Jakarta EE 11 / CDI / JAX-RS equivalents.

Load [references/annotation-map.md](../references/annotation-map.md) before starting. It contains the complete annotation mapping tables for DI, REST, Data, Security, Cache, Scheduling, and Lifecycle.

## What to do

- [ ] Migrate entities (standard JPA 3.2 — `@Entity`, `@Id`, `@GeneratedValue`)
- [ ] Migrate repositories (CDI `@ApplicationScoped` beans with `EntityManager`)
- [ ] Migrate service layer (remove Spring stereotypes, use CDI scopes)
- [ ] Migrate controllers/resources (Spring MVC → Jakarta REST / JAX-RS)
- [ ] Migrate DI annotations (`@Autowired` → `@Inject`, `@Component`/`@Service` → `@ApplicationScoped`, etc.)
- [ ] Migrate configuration injection (`@Value` → `@ConfigProperty`)
- [ ] Migrate view layer: `Model.addAttribute()` → inject data via JAX-RS or Jakarta Faces
- [ ] Remove `@SpringBootApplication` main class
- [ ] Replace Spring's `@Transactional` with `jakarta.transaction.Transactional`
- [ ] Compile: `./mvnw clean compile -DskipTests` (Maven) or `./gradlew clean compileJava -x test` (Gradle)

Use the annotation-map.md reference for the full mapping. Below are the key patterns with before/after examples.

## Entity Layer

JPA annotations are already part of Jakarta EE — minimal changes needed. Update imports from `javax.persistence.*` to `jakarta.persistence.*`.

```java
// BEFORE: Spring Data JPA (javax.persistence)
import javax.persistence.*;

@Entity
public class Todo {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String title;
    private boolean completed;
    // getters + setters
}

// AFTER: Jakarta JPA 3.2 (jakarta.persistence)
import jakarta.persistence.*;

@Entity
public class Todo {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String title;
    private boolean completed;
    // getters + setters — standard Java bean style retained
}
```

## Repository Layer

Spring Data repositories (`JpaRepository`, `CrudRepository`) have no direct Jakarta EE equivalent. Replace with CDI beans that inject `EntityManager`:

```java
// BEFORE: Spring Data JPA repository
public interface TodoRepository extends JpaRepository<Todo, Long> {
    List<Todo> findByCompleted(boolean completed);
}

// AFTER: Jakarta EE CDI repository with EntityManager
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.transaction.Transactional;

@ApplicationScoped
public class TodoRepository {

    @PersistenceContext
    private EntityManager em;

    public List<Todo> findAll() {
        return em.createQuery("SELECT t FROM Todo t", Todo.class).getResultList();
    }

    public List<Todo> findByCompleted(boolean completed) {
        return em.createQuery(
                "SELECT t FROM Todo t WHERE t.completed = :completed", Todo.class)
                .setParameter("completed", completed)
                .getResultList();
    }

    public Optional<Todo> findById(Long id) {
        return Optional.ofNullable(em.find(Todo.class, id));
    }

    @Transactional
    public Todo save(Todo todo) {
        if (todo.getId() == null) {
            em.persist(todo);
            return todo;
        }
        return em.merge(todo);
    }

    @Transactional
    public void deleteById(Long id) {
        findById(id).ifPresent(em::remove);
    }
}
```

### persistence.xml

Create `src/main/resources/META-INF/persistence.xml` if it does not exist:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<persistence version="3.2"
             xmlns="https://jakarta.ee/xml/ns/persistence"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="https://jakarta.ee/xml/ns/persistence
                                 https://jakarta.ee/xml/ns/persistence/persistence_3_2.xsd">
    <persistence-unit name="defaultPU" transaction-type="JTA">
        <properties>
            <!-- Schema generation — equivalent to spring.jpa.hibernate.ddl-auto -->
            <property name="jakarta.persistence.schema-generation.database.action" value="drop-and-create"/>
            <!-- Optional: set naming strategy to match Spring Boot's snake_case default -->
            <property name="hibernate.physical_naming_strategy"
                      value="org.hibernate.boot.model.naming.CamelCaseToUnderscoresNamingStrategy"/>
        </properties>
    </persistence-unit>
</persistence>
```

## Service Layer

```java
// BEFORE: Spring — interface + impl
public interface TodoService { List<Todo> findAll(); }

@Service
public class TodoServiceImpl implements TodoService {
    @Autowired private TodoRepository repository;
    @Override public List<Todo> findAll() { return repository.findAll(); }
}

// AFTER: Jakarta EE CDI — single @ApplicationScoped class
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class TodoService {
    @Inject
    TodoRepository repository;

    public List<Todo> findAll() { return repository.findAll(); }
}
```

**Decision guide:**
- Service only delegates to repository → eliminate it, inject repository directly in the resource
- Service has real business logic → keep as `@ApplicationScoped`, remove the interface
- Interface used for testing/mocking → not needed, Mockito and CDI `@Alternative` both work on concrete classes

## Controller → JAX-RS Resource

```java
// BEFORE: Spring MVC REST controller
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/todos")
public class TodoController {

    @Autowired private TodoService todoService;

    @GetMapping
    public List<Todo> list() {
        return todoService.findAll();
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Todo create(@RequestBody Todo todo) {
        return todoService.save(todo);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        todoService.deleteById(id);
    }
}

// AFTER: Jakarta REST (JAX-RS 4.0)
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.*;

@Path("/api/todos")
@ApplicationScoped
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class TodoResource {

    @Inject
    TodoService todoService;

    @GET
    public List<Todo> list() {
        return todoService.findAll();
    }

    @POST
    public Response create(Todo todo) {
        Todo created = todoService.save(todo);
        return Response.status(Response.Status.CREATED).entity(created).build();
    }

    @DELETE
    @Path("/{id}")
    public Response delete(@PathParam("id") Long id) {
        todoService.deleteById(id);
        return Response.noContent().build();
    }
}
```

### JAX-RS Application class

Create a JAX-RS `Application` class to set the base path (equivalent to `server.servlet.context-path`):

```java
import jakarta.ws.rs.ApplicationPath;
import jakarta.ws.rs.core.Application;

@ApplicationPath("/")
public class RestApplication extends Application {
    // No body needed — CDI + JAX-RS auto-discovers resources
}
```

## Dependency Injection (CDI 4.1)

```java
// BEFORE: Spring DI
@Component
public class MyBean { ... }

@Service
public class MyService {
    @Autowired private MyBean bean;
    @Value("${app.name}") private String appName;
}

// AFTER: CDI 4.1
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;

@ApplicationScoped
public class MyBean { ... }

@ApplicationScoped
public class MyService {
    @Inject MyBean bean;
    @Inject @ConfigProperty(name = "app.name") String appName;
}
```

## Main Class Removal

If the main class **only** contains `SpringApplication.run(...)`, delete it entirely — Jakarta EE applications do not need a main class. The application server (Open Liberty) manages lifecycle.

If it contains additional logic, migrate before deleting:

- `@Bean` methods → move to an `@ApplicationScoped` class with CDI `@Produces`
- `CommandLineRunner` / `ApplicationRunner` → CDI startup event observer
- `@EnableScheduling`, `@EnableCaching`, etc. → not needed, enabled via Liberty features in `server.xml`

### @Bean methods → CDI @Produces

```java
// BEFORE: Spring @Bean in main class
@SpringBootApplication
public class MyApp {
    public static void main(String[] args) { SpringApplication.run(MyApp.class, args); }

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper().registerModule(new JavaTimeModule());
    }
}

// AFTER: CDI @Produces in a dedicated class
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;

@ApplicationScoped
public class AppConfig {
    @Produces
    @ApplicationScoped
    public ObjectMapper objectMapper() {
        return new ObjectMapper().registerModule(new JavaTimeModule());
    }
}
```

### CommandLineRunner → CDI StartupEvent observer

```java
// BEFORE: Spring CommandLineRunner
@SpringBootApplication
public class MyApp implements CommandLineRunner {
    @Autowired DataLoader dataLoader;
    public static void main(String[] args) { SpringApplication.run(MyApp.class, args); }
    @Override public void run(String... args) { dataLoader.seed(); }
}

// AFTER: CDI startup event observer
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.enterprise.event.Startup;
import jakarta.inject.Inject;

@ApplicationScoped
public class StartupObserver {
    @Inject DataLoader dataLoader;

    public void onStart(@Observes Startup event) {
        dataLoader.seed();
    }
}
```

## Watch out

- **`jakarta.*` imports**: All `javax.*` imports must become `jakarta.*` in Jakarta EE 10+. Verify every import.
- **`@Transactional`**: Use `jakarta.transaction.Transactional`, NOT `org.springframework.transaction.annotation.Transactional`.
- **No component scanning**: CDI discovers beans in the same archive via `beans.xml` or by default if the archive is a bean archive (JAR/WAR with CDI 4.0+ implicit discovery). Add `src/main/resources/META-INF/beans.xml` with `bean-discovery-mode="all"` if beans are not discovered.
- **No Open Session in View**: Liberty/JPA does not keep the persistence context open across the entire HTTP request by default. Lazy-loaded associations must be fetched within a `@Transactional` boundary.
- **JAX-RS path conflicts**: Unlike Spring, JAX-RS does not allow overlapping `@Path` values. Check for duplicate paths.
- **JSON serialization**: Liberty uses JSON-B 3.0 by default (not Jackson). If the app relies on Jackson-specific annotations (`@JsonProperty`, `@JsonIgnore`), add `jackson-jakarta-rs-json-provider` or configure a JAX-RS `ContextResolver<ObjectMapper>`.
