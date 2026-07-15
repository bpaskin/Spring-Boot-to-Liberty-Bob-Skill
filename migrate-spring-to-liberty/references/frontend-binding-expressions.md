# Replacing Spring MVC binding expressions

Load this reference during a rewrite when a controller or template uses Spring MVC form binding. Apply it with the contract-selected frontend reference; do not use it for a retain-Spring rehost.

## Contents

- [Detect and characterize](#detect-and-characterize)
- [Replace controller binding](#replace-controller-binding)
- [Replace view expressions](#replace-view-expressions)
- [Protect the binding boundary](#protect-the-binding-boundary)
- [Verify and clean up](#verify-and-clean-up)

## Detect and characterize

Inspect controllers, templates, validators, converters, tests, and message bundles for:

- `@ModelAttribute`, `BindingResult`, `Errors`, `@InitBinder`, `WebDataBinder`, `Formatter`, `Converter`, and `PropertyEditor`;
- Thymeleaf `th:object`, `th:field="*{...}"`, `th:errors`, `th:errorclass`, `#fields`, Spring request-context objects, and Spring Security dialect attributes;
- JSP Spring tag libraries, `<form:form modelAttribute="...">`, `<form:input path="...">`, `<form:select>`, `<form:checkboxes>`, `<form:errors>`, and `<spring:bind>`;
- dotted/nested paths, indexed collections, maps, checkboxes, multipart fields, hidden field markers, date/number formats, locale/time zone, and global errors.

Do not classify ordinary `${...}` output or `*{...}` selection syntax as Spring-owned without the rendering engine and dialect evidence. Do not replace expressions independently of the controller that creates and validates their model.

Record one binding manifest per form:

| Evidence | Record |
|---|---|
| Model root | Attribute name, DTO type, constructor/default values, and lifecycle |
| Accepted input | Exact field names, nested/indexed paths, HTTP method, encoding, and multipart parts |
| Binding policy | Allowed/disallowed fields, field-marker/default prefixes, empty-string/null behavior, and auto-growth limits |
| Conversion | Trim rules, enums, dates, numbers, locale/time zone, custom converters/editors, and conversion error codes |
| Validation | Bean Validation groups, custom validators, cross-field rules, field/global errors, message keys, and ordering |
| Redisplay | Submitted values, selected/checked state, escaping, error CSS/ARIA, focus, redirect/flash behavior, and CSRF |

Mark the form `BLOCKED` when an `@InitBinder`, converter/editor, nested collection rule, or validation path affects behavior but has no confirmed replacement. Preserve the original controller/template together until the replacement passes.

## Replace controller binding

Replace implicit population with an explicit request DTO and allowlisted assignment. Never bind request parameters directly into a persistence entity or a security-sensitive domain object.

For Jakarta MVC/JSP or a Servlet/controller bridge:

1. Read only the contract-listed `@FormParam` values or servlet parameters.
2. Apply the recorded normalization and conversion rules; distinguish missing, blank, and malformed values.
3. Validate the request DTO with Jakarta Bean Validation plus any explicit cross-field validator.
4. Store the submitted DTO, field errors, global errors, and message keys in `Models` or request attributes before redisplaying the form.
5. Perform the state change only when binding, validation, authorization, and CSRF checks all pass.

For Jakarta Faces, expose a dedicated form DTO from the backing bean and bind components to its properties. Use explicit Faces converters/validators for behavior that Spring supplied through a binder or conversion service. Preserve view scope, postback, messages, and navigation semantics.

For retained core Thymeleaf, make the Servlet/CDI controller own parameter extraction, conversion, validation, and the error map. Core Thymeleaf renders the resulting values; it does not recreate Spring MVC's `DataBinder`, `BindingResult`, or conversion service.

## Replace view expressions

Map each control and its corresponding error output together:

| Spring-owned source | Jakarta MVC/JSP target | Faces target | Core Thymeleaf target |
|---|---|---|---|
| `<form:form modelAttribute="todoForm">` / `th:object` with Spring binding | HTML `<form>` plus explicit request model root | `<h:form>` plus backing-bean DTO | HTML `<form>` plus explicit model variables |
| `<form:input path="title">` / `th:field="*{title}"` | `<input name="title" value="${fn:escapeXml(todoForm.title)}">` | `<h:inputText id="title" value="#{todoView.form.title}">` | `<input name="title" th:value="${todoForm.title}">` |
| `<form:checkbox path="done">` / checkbox `th:field` | Explicit checkbox `name`, `value`, and checked-state condition | `<h:selectBooleanCheckbox>` | Explicit `name`, `value`, and `th:checked` |
| `<form:select path="role">` / select `th:field` | Explicit `<option>` loop and selected comparison | `<h:selectOneMenu>` plus `<f:selectItems>` | Explicit option loop and `th:selected` |
| `<form:errors path="title">` / `th:errors` / `#fields` | Escaped field-error map output | `<h:message for="title">` | `th:if` plus escaped `th:text` from the field-error map |
| `<form:errors path="*">` | Escaped global-error list | `<h:messages globalOnly="true">` | Explicit global-error iteration |
| `<spring:bind>` and `status.value/error/errorMessages` | Explicit submitted-value and error model entries | Component value/message state | Explicit submitted-value and error model entries |

Preserve the original field names when clients, JavaScript, tests, or downstream handlers depend on them. For dotted or indexed paths, define an explicit flattening/reconstruction rule and cap collection sizes; never reproduce unbounded Spring auto-growth. Recreate error classes, `aria-invalid`, `aria-describedby`, and escaped submitted values so a validation failure remains usable and safe.

Do not blindly rewrite `${...}` to `#{...}` or `*{...}` to `${...}`. The target expression depends on the selected view technology, model owner, lifecycle, and escaping rules.

## Protect the binding boundary

- Allowlist writable request DTO fields and reject or ignore server-managed fields such as IDs, roles, tenant IDs, ownership, prices, and audit attributes according to the baseline contract.
- Test over-posting with an unapproved field. It must not change domain state.
- Preserve CSRF enforcement before processing state-changing form data.
- Escape redisplayed values and messages. Treat intentionally raw HTML as a reviewed exception.
- Preserve authorization checks independently of form-field visibility; hiding a control is not access control.
- Set explicit maximum sizes for indexed collections, multipart parts, and text fields where Spring previously supplied limits.

## Verify and clean up

Test initial GET, valid submit, every representative field validation failure, conversion failure, global/cross-field failure, checkbox absence, select/list binding, nested/indexed input, rejected over-posting, valid/missing/invalid CSRF, redirect, and refresh/resubmit behavior. Compare status, route, rendered values, messages, escaping, and resulting state with the baseline.

For complete Spring removal, search the migrated slice for `BindingResult`, `WebDataBinder`, `@InitBinder`, Spring form-tag URIs, `<form:* path=...>`, `<spring:bind>`, `th:field`, `th:errors`, `#fields`, and Spring request-context objects. Remove a Spring MVC or Thymeleaf-Spring dependency only after none of its retained slices use those facilities. Record staged exceptions instead of claiming the expressions were migrated.
