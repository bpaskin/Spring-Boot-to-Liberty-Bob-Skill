# Module: Frontend / View Layer

Migrate templates, static assets, and view-related code from Spring MVC + Thymeleaf to a Jakarta EE view technology.

## What to do

- [ ] Detect the view layer scenario (see **Detection** below) — this determines the entire path through this module
- [ ] Apply the path for the detected scenario — only one path executes
- [ ] Move static resources from `static/` to `src/main/webapp/` (WAR convention)
- [ ] Remove Spring CSRF tokens from HTML and JavaScript (Liberty uses its own CSRF support)
- [ ] Update controller/resource classes to use the chosen technology
- [ ] Compile: `./mvnw clean compile -DskipTests` (Maven) or `./gradlew clean compileJava -x test` (Gradle)

---

## Detection

Inspect the project and classify it into **one** of three scenarios:

| Scenario | Signals | Path |
|---|---|---|
| **A — Spring MVC + Thymeleaf** | `@Controller` classes returning view names + Thymeleaf templates in `src/main/resources/templates/` | Ask the user the [View Technology Decision](#view-technology-decision) — wait for answer |
| **B — Thymeleaf only (no Spring MVC `@Controller`)** | Thymeleaf templates present, but controllers are `@RestController` or Thymeleaf is used outside Spring MVC | Default to **JSP + JSTL** unless Jakarta Faces is already required elsewhere in the app |
| **C — REST only** | Only `@RestController`, no templates, no `Model`/`ModelAndView` | Skip to [REST-only](#rest-only-restcontroller--jax-rs--json-b) — no template migration needed |

> **"Jakarta Faces already required elsewhere"** means the app has a dependency on `jakarta.faces`, an existing `.xhtml` Facelets template, or the user has already chosen Faces for another part of the migration. In that case, use Faces for consistency rather than introducing a second view technology.

---

## View Technology Decision

**Scenario A only — skip this section for Scenarios B and C.**

When Spring MVC `@Controller` classes are detected, present the following to the user and **stop — do not proceed until the user has answered**:

---

> **Your Spring Boot application uses Spring MVC with server-rendered views. On Open Liberty you have two options for the view layer. Here are the trade-offs:**
>
> ### Option A — Jakarta MVC 2.1 + Eclipse Krazo
>
> **Pros**
> - Closest conceptual match to Spring MVC — action-based controllers, same request/response mental model
> - `@Controller`, `@GET`/`@POST`, `@Path` map almost 1:1 to Spring's `@Controller` + `@GetMapping`
> - Templates (Facelets or JSP) remain server-side rendered; migration is mechanical
> - `@Valid` on form beans works identically
> - URL routing is explicit and flexible (full JAX-RS `@Path` expressions)
>
> **Cons**
> - Jakarta MVC is **not** part of the Jakarta EE Platform or Web Profile — it is a standalone spec
> - Requires adding **Eclipse Krazo** as a runtime dependency (extra JAR, extra dependency to manage)
> - Smaller community, fewer Open Liberty guides and examples
> - Less mature tooling support compared to Faces
>
> **What you add to your project:**
> ```xml
> <!-- pom.xml — Jakarta MVC API (compile-time, provided by Krazo at runtime) -->
> <dependency>
>     <groupId>jakarta.mvc</groupId>
>     <artifactId>jakarta.mvc-api</artifactId>
>     <version>3.0.0</version>
>     <scope>provided</scope>
> </dependency>
> <!-- Krazo RESTEasy runtime (Liberty uses RESTEasy under restfulWS-4.0) -->
> <dependency>
>     <groupId>org.eclipse.krazo</groupId>
>     <artifactId>krazo-resteasy</artifactId>
>     <version>4.0.0</version>
> </dependency>
> ```
> ```xml
> <!-- server.xml features needed -->
> <feature>restfulWS-4.0</feature>
> <feature>jsonb-3.0</feature>
> <feature>jsonp-2.1</feature>
> <feature>cdi-4.1</feature>
> <feature>beanValidation-3.1</feature>
> <feature>pages-4.0</feature>  <!-- if using JSP/Facelets as the view -->
> ```
>
> ---
>
> ### Option B — Jakarta Faces 4.1 (JSF) + CDI
>
> **Pros**
> - Ships with Open Liberty — **zero extra dependencies**, no additional JARs required
> - Best-supported and most documented server-side view technology on Liberty
> - Rich component library ecosystem (PrimeFaces, OmniFaces)
> - Excellent for form-heavy, CRUD-style, stateful UIs
> - Built-in AJAX support (`<f:ajax>`) without writing JavaScript
>
> **Cons**
> - **Component-based model** — fundamentally different from Spring MVC's action-based model; requires learning Facelets and the JSF component lifecycle
> - URL routing is less flexible; complex URL patterns require extra configuration
> - Mixing Faces pages with REST endpoints in the same app can be awkward
> - Navigation model (outcome strings, `faces-redirect`) differs significantly from Spring's `redirect:/path`
>
> **What you add to your project:**
> ```xml
> <!-- server.xml — single feature, no pom.xml change -->
> <feature>faces-4.1</feature>
> ```
>
> ---
>
> **Which would you like to use?**
> - **A) Jakarta MVC + Krazo** — closest migration path from Spring MVC, action-based
> - **B) Jakarta Faces + CDI** — no extra dependencies, Liberty-native, component-based

---

**Wait for the user's answer before continuing. Record the choice and use it for all subsequent steps in this module and in `code.md`.**

---

## Option A — Jakarta MVC 2.1 + Eclipse Krazo

### Dependency / Feature

> **Always verify the latest versions from Maven Central before adding these dependencies:**
> - `jakarta.mvc-api`: https://search.maven.org/artifact/jakarta.mvc/jakarta.mvc-api
> - `krazo-resteasy`: https://search.maven.org/artifact/org.eclipse.krazo/krazo-resteasy
>
> The versions below were current as of the last skill update. Check that they are still the latest release before writing to `pom.xml`.

Add Krazo to `pom.xml`:

```xml
<!-- pom.xml — Jakarta MVC API (provided scope; Krazo supplies the implementation) -->
<dependency>
    <groupId>jakarta.mvc</groupId>
    <artifactId>jakarta.mvc-api</artifactId>
    <version>3.0.0</version>
    <scope>provided</scope>
</dependency>
<!-- Krazo RESTEasy runtime (Liberty uses RESTEasy under restfulWS-4.0) -->
<dependency>
    <groupId>org.eclipse.krazo</groupId>
    <artifactId>krazo-resteasy</artifactId>
    <version>4.0.0</version>
</dependency>
```

Add features to `server.xml`:
```xml
<featureManager>
    <feature>restfulWS-4.0</feature>
    <feature>jsonb-3.0</feature>
    <feature>jsonp-2.1</feature>
    <feature>cdi-4.1</feature>
    <feature>beanValidation-3.1</feature>
    <feature>pages-4.0</feature>
</featureManager>
```

### Controller → Jakarta MVC Controller

```java
// BEFORE: Spring MVC @Controller
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

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

// AFTER: Jakarta MVC @Controller
import jakarta.inject.Inject;
import jakarta.mvc.Controller;
import jakarta.mvc.Models;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;

@Path("/todos")
@Controller
public class TodoController {

    @Inject
    private Models models;       // replaces Spring's Model

    @Inject
    private TodoService todoService;

    @GET
    public String list() {
        models.put("todos", todoService.findAll());
        return "todos.jsp";      // resolved relative to /WEB-INF/views/
    }

    @POST
    @Consumes(MediaType.APPLICATION_FORM_URLENCODED)
    public String create(@BeanParam Todo todo) {
        todoService.save(todo);
        return "redirect:/todos";
    }
}
```

### Thymeleaf → JSP (Jakarta MVC)

Jakarta MVC renders views from `src/main/webapp/WEB-INF/views/` by default.

| Thymeleaf | JSP (Jakarta MVC) | Notes |
|---|---|---|
| `th:text="${name}"` | `${name}` (EL) | Standard EL |
| `th:each="item : ${items}"` | `<c:forEach var="item" items="${items}">` | JSTL core |
| `th:if="${condition}"` | `<c:if test="${condition}">` | JSTL conditional |
| `th:action="@{/submit}"` | `<form action="${pageContext.request.contextPath}/submit" method="post">` | Standard HTML form |
| `th:value="${value}"` | `<input value="${value}"/>` | Standard HTML input |

Place views at:
```
src/main/webapp/WEB-INF/views/todos.jsp
```

---

## Option B — Jakarta Faces 4.1 (JSF) + CDI

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

## Scenario B — Thymeleaf without Spring MVC (`@Controller`) → JSP + JSTL

Use this path when Thymeleaf templates are present but the controllers are `@RestController` (or Thymeleaf was used as a standalone renderer outside Spring MVC). The default replacement is **JSP + JSTL** — it is the closest Thymeleaf equivalent in syntax and requires no extra dependencies beyond the `pages-4.0` Liberty feature.

**Exception**: if Jakarta Faces is already required elsewhere in the app (existing `.xhtml` templates, `faces-4.1` feature, or a prior decision to use Faces), migrate to Facelets instead for consistency.

### Feature required

```xml
<!-- server.xml -->
<featureManager>
    <feature>pages-4.0</feature>   <!-- includes JSP 4.0 + JSTL 3.0 + EL 6.0 -->
</featureManager>
```

No extra Maven/Gradle dependency — Liberty provides the JSP and JSTL implementation.

### Template file location

```
# BEFORE (Spring Boot — Thymeleaf)
src/main/resources/templates/todos.html

# AFTER (Liberty WAR — JSP)
src/main/webapp/WEB-INF/views/todos.jsp
```

### Thymeleaf → JSP + JSTL syntax mapping

| Thymeleaf | JSP + JSTL | Notes |
|---|---|---|
| `th:text="${name}"` | `${name}` | Standard EL — direct equivalent |
| `th:utext="${html}"` | `${html}` | Unescaped output — same in JSP |
| `th:each="item : ${items}"` | `<c:forEach var="item" items="${items}">` | Requires `<%@ taglib uri="jakarta.tags.core" prefix="c" %>` |
| `th:if="${condition}"` | `<c:if test="${condition}">` | JSTL conditional |
| `th:unless="${condition}"` | `<c:if test="${!condition}">` | Negate the expression |
| `th:switch` / `th:case` | `<c:choose>` / `<c:when>` / `<c:otherwise>` | JSTL choose |
| `th:href="@{/path}"` | `<a href="${pageContext.request.contextPath}/path">` | Use `contextPath` for WAR-relative links |
| `th:action="@{/submit}"` | `<form action="${pageContext.request.contextPath}/submit" method="post">` | Standard HTML form |
| `th:value="${val}"` | `<input value="${val}"/>` | Standard HTML attribute |
| `th:src="@{/js/app.js}"` | `<script src="${pageContext.request.contextPath}/js/app.js">` | Static asset reference |
| `th:fragment="name"` + `th:replace` | `<%@ include file="fragment.jsp" %>` or `<jsp:include page="..."/>` | Layout/include mechanism |
| `th:with="x=${expr}"` | `<c:set var="x" value="${expr}"/>` | Local variable |

### JSTL taglib declarations

Add to the top of each JSP that uses JSTL:

```jsp
<%@ taglib uri="jakarta.tags.core"     prefix="c"   %>  <!-- core: forEach, if, choose, set -->
<%@ taglib uri="jakarta.tags.fmt"      prefix="fmt" %>  <!-- formatting: formatDate, formatNumber -->
<%@ taglib uri="jakarta.tags.functions" prefix="fn" %>  <!-- functions: fn:length, fn:contains -->
```

### Before / After example

```jsp
<%-- BEFORE: Thymeleaf todos.html --%>
<html xmlns:th="http://www.thymeleaf.org">
<body>
    <ul>
        <li th:each="todo : ${todos}" th:text="${todo.title}"></li>
    </ul>
    <p th:if="${todos.empty}">No todos yet.</p>
</body>
</html>

<%-- AFTER: JSP todos.jsp --%>
<%@ taglib uri="jakarta.tags.core" prefix="c" %>
<html>
<body>
    <ul>
        <c:forEach var="todo" items="${todos}">
            <li>${todo.title}</li>
        </c:forEach>
    </ul>
    <c:if test="${empty todos}">
        <p>No todos yet.</p>
    </c:if>
</body>
</html>
```

### Forwarding to a JSP from a JAX-RS resource

JSPs must be forwarded to via a Servlet — JAX-RS cannot return a JSP directly. Use a thin `@WebServlet` or a Servlet `RequestDispatcher` forward:

```java
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.inject.Inject;

@WebServlet("/todos")
public class TodoServlet extends HttpServlet {

    @Inject
    private TodoService todoService;

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        req.setAttribute("todos", todoService.findAll());
        req.getRequestDispatcher("/WEB-INF/views/todos.jsp").forward(req, resp);
    }
}
```

> **Note**: If the original Spring MVC `@Controller` used `Model.addAttribute()` and returned a view name, the `@WebServlet` pattern above is the direct structural equivalent on Jakarta EE without adopting a full MVC framework.

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

If the app needs CSRF protection on Liberty, enable the `appSecurity-6.0` feature and configure `<csrfProtection>` in `server.xml`, or use the MicroProfile JWT (`mpJwt-2.1`) feature for stateless API security.

## REST-only (`@RestController` → JAX-RS + JSON-B)

If the app uses only `@RestController` — no `Model`, no templates, no server-rendered HTML — skip Options A and B entirely. The migration is handled in [`code.md`](code.md) via the standard JAX-RS resource pattern. No frontend module action is needed beyond moving any static assets.

---

## Watch out

- **Jakarta MVC (Krazo)**: Views are resolved from `/WEB-INF/views/` by default — create that directory and place templates there
- **Krazo + Faces**: Do not mix Jakarta MVC and Jakarta Faces in the same application — choose one
- **Faces needs `WEB-INF/faces-config.xml`** (optional in Faces 4.1, but required if using navigation rules or custom converters)
- **`@Named` vs `@ManagedBean`**: Always use CDI `@Named` — `@ManagedBean` is removed in Jakarta Faces 4.0
- **EL scope**: Faces EL (`#{...}`) resolves CDI beans. Spring's `${...}` SpEL does not apply
- **JSP requires `pages-4.0`** feature in `server.xml`; ensure the feature is declared
- **Context root**: Liberty WAR context root defaults to `/<artifactId>`. Set `contextRoot="/"` in `server.xml` if needed
