# Server-rendered views with Jakarta Faces

Load this reference only when the migration contract selects Jakarta Faces for Spring MVC views.

## Contents

- [Runtime](#runtime)
- [Backing-bean mapping](#backing-bean-mapping)
- [Facelets migration](#facelets-migration)
- [Security and verification](#security-and-verification)

## Runtime

Use Liberty's Faces and CDI features; do not package another Faces implementation:

```xml
<featureManager>
    <feature>faces-4.1</feature>
    <feature>cdi-4.1</feature>
    <feature>validation-3.1</feature>
</featureManager>
```

Add persistence, security, or other features only when the application requires them.

## Backing-bean mapping

Faces is component-based, so do not pretend every Spring MVC controller maps one-to-one. Group state and actions by view:

```java
@Named
@ViewScoped
public class TodoView implements Serializable {
    private static final long serialVersionUID = 1L;

    private final TodoService service;
    private List<Todo> todos;

    @Inject
    public TodoView(TodoService service) {
        this.service = service;
    }

    public void load() {
        todos = service.findAll();
    }

    public List<Todo> getTodos() {
        return todos;
    }
}
```

Choose CDI scope from actual lifecycle needs. Make view-scoped beans serializable and avoid storing non-serializable request resources as conversational state. Map redirects/navigation, validation, converters, messages, locale, and exception behavior explicitly.

## Facelets migration

Place Facelets under `src/main/webapp/` and use `.xhtml`. Typical mappings:

| Thymeleaf/Spring MVC | Faces |
|---|---|
| model attribute | bean property via `#{todoView.todos}` |
| `th:each` | `ui:repeat` or `h:dataTable` |
| form binding | `h:form` plus input components |
| validation errors | `h:message` / `h:messages` |
| fragments/layouts | Facelets composition/templates |
| controller POST | component action/actionListener |

Do not translate `${...}` blindly; Faces deferred expressions normally use `#{...}`. Preserve escaping and verify any intentionally raw HTML.

## Security and verification

Faces supplies view-state protection but that does not replace a full security review. Verify state-changing forms reject missing/invalid state or CSRF material as appropriate, and preserve authentication and authorization behavior through Jakarta Security.

Test initial GET, postback, validation failure, navigation/redirect, expired view, anonymous access, forbidden access, and static resources. Compare behavior with the baseline rather than only checking that a page renders.
