# Module: Frontend / View Layer

Migrate templates, static assets, and view-related code from Spring MVC + Thymeleaf to a Jakarta EE view technology.

## What to do

- [ ] Choose the target view technology (see below)
- [ ] Convert Thymeleaf templates to the chosen technology
- [ ] Move static resources from `static/` to `src/main/webapp/` (WAR convention)
- [ ] Remove Spring CSRF tokens from HTML and JavaScript (Liberty uses its own CSRF support)
- [ ] Update controller/resource classes to use the new view technology
- [ ] Compile: `./mvnw clean compile -DskipTests` (Maven) or `./gradlew clean compileJava -x test` (Gradle)

## Choose a View Technology

| Technology | Best for | Liberty feature |
|---|---|---|
| **Jakarta Faces (JSF) 4.1** | Form-heavy, stateful UIs; direct Spring MVC equivalent | `faces-4.1` |
| **JAX-RS + JSON-B** (REST) | APIs consumed by a JavaScript front-end | `restfulWS-4.0` + `jsonb-3.0` |
| **Jakarta Server Pages (JSP)** | Simple template pages; similar to Thymeleaf layout | `pages-4.0` (included in `jakartaee-11.0`) |

For most Spring MVC `@Controller` + Thymeleaf apps, **Jakarta Faces** is the closest semantic equivalent. For `@RestController` apps, **JAX-RS + JSON-B** is a direct replacement.

## Thymeleaf → Jakarta Faces (JSF 4.1)

Jakarta Faces uses Facelets (`.xhtml`) as the template language.

### Dependency / Feature

Add the Faces feature to `server.xml`:
```xml
<featureManager>
    <feature>faces-4.1</feature>
    <!-- or use the jakartaee-11.0 umbrella which includes faces -->
</featureManager>
```

No extra Maven/Gradle dependency is needed — Liberty supplies the implementation.

### Controller → Backing Bean

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

// AFTER: Jakarta Faces Backing Bean
import jakarta.enterprise.context.RequestScoped;
import jakarta.faces.context.FacesContext;
import jakarta.inject.Inject;
import jakarta.inject.Named;

@Named          // EL name defaults to "todoController"
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

### Thymeleaf → Facelets Syntax

| Thymeleaf | Facelets (JSF 4.1) | Notes |
|---|---|---|
| `th:text="${name}"` | `#{todoController.name}` | EL expression |
| `th:each="item : ${items}"` | `<ui:repeat value="#{todoController.todos}" var="item">` | Loop |
| `th:if="${condition}"` | `<h:panelGroup rendered="#{condition}">` | Conditional render |
| `th:href="@{/path/{id}(id=${item.id})}"` | `<h:link outcome="/path/#{item.id}">` | Navigation link |
| `th:action="@{/submit}"` | `<h:form>` with `<h:commandButton action="...">` | Form submit |
| `th:value="${value}"` | `<h:inputText value="#{bean.value}"/>` | Input binding |

### Facelets Template Location

Facelets pages go in `src/main/webapp/`:
```
src/main/webapp/todos.xhtml
src/main/webapp/WEB-INF/templates/layout.xhtml
```

## Thymeleaf → Jakarta Server Pages (JSP)

If the app is primarily view-only and Thymeleaf was used for simple interpolation, JSP is the lightest migration path.

```jsp
<!-- BEFORE: Thymeleaf todos.html -->
<ul th:each="todo : ${todos}">
    <li th:text="${todo.title}"></li>
</ul>

<!-- AFTER: JSP todos.jsp (set by forward from JAX-RS or Servlet) -->
<%@ taglib uri="jakarta.tags.core" prefix="c" %>
<ul>
    <c:forEach var="todo" items="${todos}">
        <li>${todo.title}</li>
    </c:forEach>
</ul>
```

## Static Assets

```
# BEFORE (Spring Boot)
src/main/resources/static/css/style.css
src/main/resources/static/js/app.js

# AFTER (Liberty WAR)
src/main/webapp/css/style.css
src/main/webapp/js/app.js
```

Static files placed in `src/main/webapp/` are served at the WAR's context root automatically.

## CSRF Token Removal

Spring Security injects `_csrf` tokens into Thymeleaf templates. Remove these — they have no Jakarta EE equivalent in the same form:

```html
<!-- DELETE from HTML: -->
<meta name="_csrf" th:content="${_csrf.token}"/>
<meta name="_csrf_header" th:content="${_csrf.headerName}"/>
<input type="hidden" th:name="${_csrf.parameterName}" th:value="${_csrf.token}"/>
```

```javascript
// DELETE from JS:
const token = document.querySelector('meta[name="_csrf"]').content;
const header = document.querySelector('meta[name="_csrf_header"]').content;
headers[header] = token;
```

If the app needs CSRF protection on Liberty, enable the `appSecurity-5.0` feature and configure `<csrfProtection>` in `server.xml`, or use the MicroProfile JWT (`mpJwt-2.1`) feature for stateless API security.

## Watch out

- **Faces needs `WEB-INF/faces-config.xml`** (optional in Faces 4.1, but required if using navigation rules or custom converters)
- **`@Named` vs `@ManagedBean`**: Always use CDI `@Named` — `@ManagedBean` is removed in Jakarta Faces 4.0
- **EL scope**: Faces EL (`#{...}`) resolves CDI beans. Spring's `${...}` SpEL does not apply
- **JSP requires `pages-4.0`** feature in `server.xml`; ensure the feature is declared
- **Context root**: Liberty WAR context root defaults to `/<artifactId>`. Set `contextRoot="/"` in `server.xml` if needed
