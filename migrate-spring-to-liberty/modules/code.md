# Module: Code

Follow the shared [migration ledger and transaction protocol](../references/migration-ledger.md); migrate only the confirmed scope and resume from semantic evidence rather than annotation counts alone.

If the contract selects retain Spring and rehost, log this module as `SKIP` and stop. Spring application code must remain unchanged on the rehost path.

Migrate all Java source code from Spring patterns to Jakarta EE 11 / CDI / JAX-RS equivalents.

Load [references/annotation-map.md](../references/annotation-map.md) before starting. It contains the annotation mapping tables for DI, REST, Data, Cache, Scheduling, and Lifecycle, plus security routing guidance.
When Spring Data repository interfaces are present, also load [references/jakarta-data.md](../references/jakarta-data.md) and apply the repository strategy recorded in the migration contract.

The dedicated [security module](security.md) owns `SecurityFilterChain`, authentication mechanisms, authorization expressions, CSRF/CORS, sessions, logout, trust, and security tests. The [async/events module](async-events.md) owns `@Async`, executor configuration, application events, non-default transaction semantics, Spring Retry/listeners, and their failure tests. Inventory these references here, but do not migrate or remove them in this module.

## What to do

- [ ] Migrate entities (standard JPA 3.2 — `@Entity`, `@Id`, `@GeneratedValue`)
- [ ] Migrate repositories with the contract-selected Jakarta Data 1.0 or CDI + `EntityManager` strategy
- [ ] Migrate service layer (remove Spring stereotypes, use CDI scopes)
- [ ] Migrate controllers/resources — approach depends on view technology choice (see **Controller Migration** below)
- [ ] Migrate DI annotations (`@Autowired` → `@Inject`, `@Component`/`@Service` → `@ApplicationScoped`, etc.)
- [ ] Migrate configuration injection (`@Value` → `@ConfigProperty`)
- [ ] Migrate view layer: `Model.addAttribute()` → Jakarta MVC `Models`, Jakarta Faces backing bean, or JAX-RS response
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

Jakarta EE 11 includes Jakarta Data 1.0, which can preserve a repository-interface style for supported Spring Data patterns. It is not a drop-in Spring Data implementation: inventory inherited CRUD calls, derived queries, pagination, sorting, projections, specifications, custom fragments, auditing, locking, and exception assumptions before choosing a strategy.

Use the repository strategy from the migration contract:

- **Jakarta Data 1.0** for straightforward CRUD and supported automatic or annotated queries. On Open Liberty, enable `data-1.0` plus `persistence-3.2` for Jakarta Persistence entities. Do not use `dataContainer-1.0` unless a separate Jakarta Data provider is intentionally configured.
- **CDI + `EntityManager`** for complex or provider-specific behavior, or when explicit query and persistence control is more important than retaining repository interfaces.
- **Staged exception** when neither path can preserve behavior in the current scope; keep the original code and record a migration TODO.

For a compatible repository, Jakarta Data can retain the interface shape:

```java
// BEFORE: Spring Data JPA repository
public interface TodoRepository extends JpaRepository<Todo, Long> {
    List<Todo> findByCompleted(boolean completed);
}

// AFTER: Jakarta Data 1.0 repository
import jakarta.data.repository.CrudRepository;
import jakarta.data.repository.Repository;

@Repository(dataStore = "TodoStore") // Must match reviewed Liberty configuration.
public interface TodoRepository extends CrudRepository<Todo, Long> {
    // Jakarta Data Query by Method Name; verify generated query behavior with a test.
    List<Todo> findByCompleted(boolean completed);
}
```

The Jakarta Data `CrudRepository` lifecycle contract differs from Spring Data. Update call sites deliberately: Jakarta Data exposes `insert`, `update`, and `save`; do not assume Spring Data batching, flush, return collection, or exception behavior. Never leave the repository on an implicit default datasource unless the migration contract explicitly selected it. Bind `dataStore` to a reviewed persistence-unit reference, datasource, or Liberty `databaseStore`, and disable automatic table creation/removal by default. See the dedicated reference for the compatibility and datastore checklists.

For the explicit persistence strategy, replace the interface with a CDI bean that injects `EntityManager`:

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
            <!-- Non-destructive default. Use a reviewed migration tool for schema changes. -->
            <property name="jakarta.persistence.schema-generation.database.action" value="none"/>
        </properties>
    </persistence-unit>
</persistence>
```

Do not translate `ddl-auto=create`, `create-drop`, or `update` into a destructive Jakarta Persistence action automatically. Record the existing behavior in the migration contract. Require the user to identify the target environment, confirm a usable backup, and approve the exact action before using `create`, `drop`, or `drop-and-create`. Prefer Flyway, Liquibase, or the project's existing reviewed schema-migration mechanism for durable environments.

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

## Controller Migration

**The approach here depends on the view technology chosen in [`frontend.md`](frontend.md).** Check the user's decision before applying any of the patterns below.

| User chose | Pattern to apply |
|---|---|
| **Jakarta MVC + Krazo** (Option A) | → [Jakarta MVC Controller](#spring-mvc-controller--jakarta-mvc-controller) |
| **Jakarta Faces + CDI** (Option B) | → [Jakarta Faces Backing Bean](#spring-mvc-controller--jakarta-faces-backing-bean) |
| **REST-only** / `@RestController` only | → [JAX-RS Resource](#restcontroller--jax-rs-resource) |

---

### Spring MVC `@Controller` → Jakarta MVC Controller

> Apply this pattern only when the user chose **Option A (Jakarta MVC + Krazo)** in `frontend.md`.

```java
// BEFORE: Spring MVC @Controller (server-rendered view)
@Controller
public class TodoController {
    @Autowired private TodoService todoService;

    @GetMapping("/todos")
    public String list(Model model) {
        model.addAttribute("todos", todoService.findAll());
        return "todos";
    }
}

// AFTER: Jakarta MVC @Controller
import jakarta.inject.Inject;
import jakarta.mvc.Controller;
import jakarta.mvc.Models;
import jakarta.ws.rs.*;

@Path("/todos")
@Controller
public class TodoController {

    @Inject
    private Models models;

    @Inject
    private TodoService todoService;

    @GET
    public String list() {
        models.put("todos", todoService.findAll());
        return "todos.jsp";   // resolved from /WEB-INF/views/
    }
}
```

---

### Spring MVC `@Controller` → Jakarta Faces Backing Bean

> Apply this pattern only when the user chose **Option B (Jakarta Faces + CDI)** in `frontend.md`.

```java
// BEFORE: Spring MVC @Controller
@Controller
public class TodoController {
    @Autowired private TodoService todoService;

    @GetMapping("/todos")
    public String list(Model model) {
        model.addAttribute("todos", todoService.findAll());
        return "todos";
    }

    @PostMapping("/todos")
    public String create(@ModelAttribute Todo todo) {
        todoService.save(todo);
        return "redirect:/todos";
    }
}

// AFTER: Jakarta Faces CDI backing bean
import jakarta.enterprise.context.RequestScoped;
import jakarta.inject.Inject;
import jakarta.inject.Named;

@Named
@RequestScoped
public class TodoController {

    @Inject
    private TodoService todoService;

    private List<Todo> todos;
    private Todo newTodo = new Todo();

    public void load() {
        todos = todoService.findAll();
    }

    public String create() {
        todoService.save(newTodo);
        newTodo = new Todo();
        return "todos?faces-redirect=true";
    }

    public List<Todo> getTodos() { return todos; }
    public void setTodos(List<Todo> todos) { this.todos = todos; }
    public Todo getNewTodo() { return newTodo; }
    public void setNewTodo(Todo newTodo) { this.newTodo = newTodo; }
}
```

---

### `@RestController` → JAX-RS Resource

> Apply this pattern for `@RestController` classes, or when the user chose **REST-only** (no server-rendered views).

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

- **Namespace conversion**: Convert only APIs that moved from Java/Jakarta EE to the `jakarta.*` namespace. Preserve Java SE and third-party packages such as `javax.sql`, `javax.naming`, `javax.crypto`, and `javax.cache`.
- **`@Transactional`**: Use `jakarta.transaction.Transactional`, NOT `org.springframework.transaction.annotation.Transactional`.
- **No component scanning**: CDI discovers beans in the same archive via `beans.xml` or by default if the archive is a bean archive (JAR/WAR with CDI 4.0+ implicit discovery). Add `src/main/resources/META-INF/beans.xml` with `bean-discovery-mode="all"` if beans are not discovered.
- **No Open Session in View**: Liberty/JPA does not keep the persistence context open across the entire HTTP request by default. Lazy-loaded associations must be fetched within a `@Transactional` boundary.
- **JAX-RS path conflicts**: Unlike Spring, JAX-RS does not allow overlapping `@Path` values. Check for duplicate paths.
- **JSON serialization**: Liberty uses JSON-B 3.0 by default (not Jackson). If the app relies on Jackson-specific annotations (`@JsonProperty`, `@JsonIgnore`), add `jackson-jakarta-rs-json-provider` or configure a JAX-RS `ContextResolver<ObjectMapper>`.
