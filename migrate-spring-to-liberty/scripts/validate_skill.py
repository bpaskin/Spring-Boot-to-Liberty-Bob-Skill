#!/usr/bin/env python3
"""Validate the migration skill's structure and high-risk invariants."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"
E2E_ROOT = REPO_ROOT / "tests" / "e2e"
AGENT_EVAL_ROOT = REPO_ROOT / "tests" / "agent-evals"
PRODUCTION_ROOT = REPO_ROOT / "tests" / "production"
INTEGRATION_LAB_ROOT = REPO_ROOT / "tests" / "integration-lab"
TOOLING_ROOT = REPO_ROOT / "tests" / "tooling"

INVALID_TEXT = {
    "<feature>beanValidation-3.1</feature>": "Jakarta EE 11 uses validation-3.1",
    "<feature>appSecurity-5.0</feature>": "Jakarta EE 11 uses appSecurity-6.0",
    "<feature>ejbLite-4.0</feature>": "use enterpriseBeansLite-4.0",
    "<feature>ejb-4.0</feature>": "use enterpriseBeans-4.0",
    "<feature>messaging-3.0</feature>": "Jakarta EE 11 uses messaging-3.1",
    "<feature>concurrent-3.0</feature>": "Jakarta EE 11 uses concurrent-3.1",
    "io.openliberty.tools:microshed-testing-liberty": "MicroShed uses org.microshed",
    "quarkus-rest": "Quarkus artifacts do not belong in a Liberty mapping",
    "@IfBuildProfile": "not a portable CDI or MicroProfile annotation",
    "@LookupIfProperty": "not a portable CDI or MicroProfile annotation",
    "MicroProfile Scheduler (`mpScheduler`)": "there is no mpScheduler feature",
    "Jakarta EE 11 mandates Java 21": "Jakarta EE 11 has a Java 17 minimum",
    "propose **21** in the consolidated contract": "the target JDK must be explicitly selected",
    "default to 21 when the project has no documented runtime policy": "the target JDK must not be defaulted",
    "have no direct Jakarta EE equivalent": "Jakarta EE 11 includes Jakarta Data 1.0",
    "Remove Spring CSRF tokens from HTML and JavaScript": "replace and test CSRF protection first",
    "LibertyServerContainerConfiguration": "MicroShed documents SharedContainerConfiguration with ApplicationContainer",
    "new LibertyServerContainer(": "MicroShed documents ApplicationContainer",
    "spring-boot-starter-ws` | `xmlBinding-4.0`": "SOAP needs an XML Web Services strategy, not only JAXB",
    "starter-data-redis` | Lettuce or Jedis client + configure `<connectionFactory>`": "Redis is not configured as a Liberty JDBC connection factory",
    "starter-data-mongodb` | `com.mongodb:mongodb-driver-sync` + `mongoDBClient`": "the stabilized server-managed Mongo feature is not a default strategic mapping",
    "starter-amqp` | `com.rabbitmq:amqp-client` + MicroProfile Reactive Messaging": "RabbitMQ requires a separately verified connector or retained client",
    "spring.cache.type=caffeine` | JCache provider dependency": "Caffeine is not mechanically converted into an unrelated JCache provider",
    "<version>3.6</version>": "the published jandex-maven-plugin release is 3.6.0",
}

REQUIRED_CANONICAL_FEATURES = {
    "servlet-6.1",
    "validation-3.1",
    "appSecurity-6.0",
    "concurrent-3.1",
    "enterpriseBeansLite-4.0",
    "enterpriseBeans-4.0",
    "messaging-3.1",
    "data-1.0",
}

REQUIRED_REHOST_FEATURES = {"springBoot-3.0", "springBoot-4.0"}

ALLOWED_DECLARED_FEATURES = REQUIRED_CANONICAL_FEATURES | {
    "appSecurity-6.0",
    "batch-2.1",
    "cdi-4.1",
    "dataContainer-1.0",
    "faces-4.1",
    "jakartaee-11.0",
    "jsonb-3.0",
    "jsonp-2.1",
    "messaging-3.1",
    "mdb-4.0",
    "microProfile-7.0",
    "mpConfig-3.1",
    "mpHealth-4.0",
    "mpFaultTolerance-4.1",
    "mpJwt-2.1",
    "openidConnectClient-1.0",
    "mpMetrics-5.1",
    "mpOpenAPI-4.0",
    "mpReactiveMessaging-3.0",
    "mpRestClient-4.0",
    "pages-4.0",
    "persistence-3.2",
    "restfulWS-4.0",
    "servlet-6.0",
    "servlet-6.1",
    "springBoot-3.0",
    "springBoot-4.0",
    "transaction-2.0",
    "validation-3.1",
    "webProfile-11.0",
    "wmqJmsClient-3.0",
    "xmlBinding-4.0",
    "xmlWS-4.0",
}

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
FEATURE_DECLARATION = re.compile(r"<feature>([^<]+)</feature>")
MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
DANGEROUS_SCHEMA_DECLARATION = re.compile(
    r'<property\s+name="jakarta\.persistence\.schema-generation\.database\.action"'
    r'\s+value="(?:drop|drop-and-create|create|create-only)"\s*/?>'
)
DANGEROUS_TABLE_DECLARATION = re.compile(r'(?:createTables|dropTables)="true"')
INLINE_LITERAL_PASSWORD = re.compile(r'password="(?!\$\{)[^"]+"')


def markdown_files() -> list[Path]:
    return sorted(REPO_ROOT.rglob("*.md"))


def validate_frontmatter(errors: list[str]) -> None:
    skill_file = SKILL_ROOT / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append("SKILL.md: missing YAML frontmatter")
        return
    try:
        frontmatter = text.split("---\n", 2)[1]
    except IndexError:
        errors.append("SKILL.md: unterminated YAML frontmatter")
        return
    keys = {
        line.split(":", 1)[0].strip()
        for line in frontmatter.splitlines()
        if line and not line[0].isspace() and ":" in line
    }
    if keys != {"name", "description"}:
        errors.append(
            "SKILL.md: frontmatter must contain only name and description; "
            f"found {sorted(keys)}"
        )


def validate_invariants(errors: list[str]) -> None:
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        if "<feature>servlet-6.0</feature>" in text and path.name != "rehost-spring.md":
            errors.append(
                f"{path.relative_to(REPO_ROOT)}: servlet-6.0 is allowed only for the Boot 3 rehost route; Jakarta EE 11 rewrites use servlet-6.1"
            )
        for invalid, reason in INVALID_TEXT.items():
            if invalid in text:
                errors.append(f"{path.relative_to(REPO_ROOT)}: {invalid!r}: {reason}")
        for feature in FEATURE_DECLARATION.findall(text):
            if feature not in ALLOWED_DECLARED_FEATURES:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: unreviewed Liberty feature "
                    f"declaration {feature!r}"
                )
        if DANGEROUS_SCHEMA_DECLARATION.search(text):
            errors.append(
                f"{path.relative_to(REPO_ROOT)}: destructive schema action appears "
                "in an executable XML example; examples must default to none"
            )
        if DANGEROUS_TABLE_DECLARATION.search(text):
            errors.append(
                f"{path.relative_to(REPO_ROOT)}: destructive Liberty table action "
                "appears in an executable example; examples must default to false"
            )
        if INLINE_LITERAL_PASSWORD.search(text):
            errors.append(
                f"{path.relative_to(REPO_ROOT)}: executable example contains an "
                "inline literal password; externalize it through a variable"
            )

    canonical = (
        SKILL_ROOT / "references" / "jakarta-ee11-liberty-features.md"
    ).read_text(encoding="utf-8")
    for feature in sorted(REQUIRED_CANONICAL_FEATURES):
        if feature not in canonical:
            errors.append(f"canonical feature reference is missing {feature}")

    rehost = (SKILL_ROOT / "modules" / "rehost-spring.md").read_text(encoding="utf-8")
    for feature in sorted(REQUIRED_REHOST_FEATURES):
        if feature not in rehost:
            errors.append(f"rehost module is missing {feature}")
    for required_text in (
        "Do not run the rewrite",
        "<springBootApplication",
        "REHOSTED — SPRING RETAINED",
    ):
        if required_text not in rehost:
            errors.append(f"rehost module is missing safety text {required_text!r}")

    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    if "Every module must have exactly one row" not in skill_text:
        errors.append("SKILL.md is missing the final ledger completeness check")
    for required_text in (
        "analyze_project.py",
        "migration-characterization.json",
        "verify_parity.py",
        "staged-migration",
        "data-xa-schema",
        "identity-observability",
        "reactive-cloud",
        "soap-nonrelational",
    ):
        if required_text not in skill_text:
            errors.append(f"SKILL.md is missing complex-migration routing {required_text!r}")

    for required_text in (
        "always require an explicit user selection",
        "less than or equal to the installed JDK",
        "When the installed JDK is higher than 25",
        "do not supply a default",
        "must not be asked again",
    ):
        if required_text not in skill_text:
            errors.append(
                f"SKILL.md is missing mandatory JDK selection guidance {required_text!r}"
            )

    jdk = (SKILL_ROOT / "modules" / "jdk.md").read_text(encoding="utf-8")
    for required_text in (
        "javac -version",
        "ALLOWED_JAVA_VERSIONS",
        "The target cannot be higher than the installed JDK",
        "Never infer or default `JAVA_VERSION`",
        "| 21 | 17, 21 |",
        "| 25 | 17, 21, 25 |",
        "| Greater than 25 | 17, 21, 25 |",
        "migration targets remain capped at 17, 21, and 25",
    ):
        if required_text not in jdk:
            errors.append(f"JDK module is missing selection guard {required_text!r}")

    security = (SKILL_ROOT / "modules" / "security.md").read_text(encoding="utf-8")
    for required_text in (
        "SecurityFilterChain",
        "Complex `@PreAuthorize`",
        "`401`",
        "`403`",
        "CSRF",
        "CORS",
        "logout",
        "mpJwt-2.1",
        "openidConnectClient-1.0",
    ):
        if required_text not in security:
            errors.append(f"security module is missing safety text {required_text!r}")

    binding_reference = (
        SKILL_ROOT / "references" / "frontend-binding-expressions.md"
    ).read_text(encoding="utf-8")
    for required_text in (
        "BindingResult",
        "@InitBinder",
        "th:field",
        "<spring:bind>",
        "Allowlist writable request DTO fields",
        "rejected over-posting",
        "Do not blindly rewrite",
        "${errors.containsKey(name)}",
        "th:text=\"${errors.get(name)}\"",
    ):
        if required_text not in binding_reference:
            errors.append(
                f"frontend binding reference is missing safety text {required_text!r}"
            )

    code = (SKILL_ROOT / "modules" / "code.md").read_text(encoding="utf-8")
    for required_text in (
        "@Observes Startup",
        "CDI bean creation can be lazy",
        '@ApplicationPath("/api")',
        '@WebServlet("/")',
    ):
        if required_text not in code:
            errors.append(f"code module is missing runtime regression guidance {required_text!r}")

    jakarta_data = (
        SKILL_ROOT / "references" / "jakarta-data.md"
    ).read_text(encoding="utf-8")
    for required_text in (
        "tablePrefix",
        '@Repository(dataStore = "jdbc/<name>")',
        "never emit or deploy `jdbc/<name>` literally",
        "Do not treat a `databaseStore` ID as an alias",
    ):
        if required_text not in jakarta_data:
            errors.append(
                f"Jakarta Data reference is missing datastore regression guidance {required_text!r}"
            )

    data_schema = (
        SKILL_ROOT / "modules" / "data-xa-schema.md"
    ).read_text(encoding="utf-8")
    for required_text in ("IllegalAccessError", "EclipseLink weaving", "final"):
        if required_text not in data_schema:
            errors.append(
                f"data/schema module is missing entity-enhancement guidance {required_text!r}"
            )

    run_local = (SKILL_ROOT / "modules" / "run-local.md").read_text(encoding="utf-8")
    for required_text in (
        "Schema is still empty after a clean startup",
        "WLPowners",
        "IllegalAccessError",
        "Core Thymeleaf field-expression errors",
    ):
        if required_text not in run_local:
            errors.append(
                f"run-local module is missing migration regression diagnostic {required_text!r}"
            )

    frontend = (SKILL_ROOT / "modules" / "frontend.md").read_text(encoding="utf-8")
    if "frontend-binding-expressions.md" not in frontend:
        errors.append("frontend module does not route Spring MVC binding expressions")
    for required_text in (
        "frontend-assets-layout-i18n.md",
        "META-INF/resources/webjars/<artifact>/<version>/...",
        "transitive static-asset graph",
        "same session",
    ):
        if required_text not in frontend:
            errors.append(
                f"frontend module is missing asset/layout/i18n guidance {required_text!r}"
            )

    frontend_parity = (
        SKILL_ROOT / "references" / "frontend-assets-layout-i18n.md"
    ).read_text(encoding="utf-8")
    for required_text in (
        "META-INF/resources/webjars/font-awesome/4.7.0/css/font-awesome.min.css",
        "do not copy that example version",
        "Do not stop after the top-level CSS returns `200`",
        "ClasspathResourceBundleMessageResolver",
        "WebConfiguration.resolveLocale()",
        "Startseite",
        "same session",
        "browser console/network failures",
    ):
        if required_text not in frontend_parity:
            errors.append(
                f"frontend parity reference is missing regression guidance {required_text!r}"
            )

    for required_text in (
        "Missing styles, icons, images, or fonts",
        "Locale switching or messages do not persist",
        "versionless `/webjars/...`",
        "German `Startseite`",
    ):
        if required_text not in run_local:
            errors.append(
                f"run-local module is missing frontend diagnostic {required_text!r}"
            )

    async_events = (SKILL_ROOT / "modules" / "async-events.md").read_text(encoding="utf-8")
    for required_text in (
        "ManagedExecutorService",
        "@ObservesAsync",
        "TransactionPhase",
        "`NESTED`",
        "RetryListener",
        "backpressure",
    ):
        if required_text not in async_events:
            errors.append(f"async/events module is missing safety text {required_text!r}")

    complexity = (SKILL_ROOT / "modules" / "complexity-gate.md").read_text(encoding="utf-8")
    for required_text in (
        "WebFlux",
        "R2DBC",
        "Spring Cloud",
        "Spring Integration",
        "custom starters",
        "Mark this module `BLOCKED`",
        "DEDICATED_MODULE",
    ):
        if required_text not in complexity:
            errors.append(f"complexity gate is missing safety text {required_text!r}")

    complex_contract = (
        SKILL_ROOT / "references" / "complex-adapter-contract.md"
    ).read_text(encoding="utf-8")
    for required_text in (
        "DETECT",
        "CHARACTERIZE",
        "VERIFY",
        "ROLL BACK OR CHECKPOINT",
        "safe_codemods.py",
        "verify_parity.py",
    ):
        if required_text not in complex_contract:
            errors.append(f"complex adapter contract is missing {required_text!r}")

    complex_modules = {
        "staged-migration.md": ("bounded slice", "full build"),
        "data-xa-schema.md": ("XA", "restart"),
        "identity-observability.md": ("JWKS", "exporter"),
        "reactive-cloud.md": ("backpressure", "Spring Cloud"),
        "soap-nonrelational.md": ("SOAP", "Redis"),
    }
    for name, markers in complex_modules.items():
        path = SKILL_ROOT / "modules" / name
        if not path.is_file():
            errors.append(f"complex adapter module is missing {name}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{name} is missing safety text {marker!r}")

    messaging = (SKILL_ROOT / "modules" / "messaging.md").read_text(encoding="utf-8")
    for required_text in ("offset", "dead-letter", "ordering", "Kafka", "JMS", "RabbitMQ"):
        if required_text not in messaging:
            errors.append(f"messaging module is missing safety text {required_text!r}")

    batch = (SKILL_ROOT / "modules" / "batch-scheduling.md").read_text(encoding="utf-8")
    for required_text in ("checkpoint", "restart", "misfire", "Quartz", "Jakarta Batch", "time zone"):
        if required_text not in batch:
            errors.append(f"batch/scheduling module is missing safety text {required_text!r}")

    deploy = (SKILL_ROOT / "modules" / "deploy.md").read_text(encoding="utf-8")
    for required_text in (
        "separate explicit authorization",
        "kernel-slim",
        "features.sh",
        "configure.sh",
        "/health/started",
        "dry-run",
        "SBOM",
    ):
        if required_text not in deploy:
            errors.append(f"deployment module is missing safety text {required_text!r}")

    feature_scan = (SKILL_ROOT / "modules" / "feature-scan.md").read_text(encoding="utf-8")
    for required_text in (
        "`jsonb-3.0` feature already enables `jsonp-2.1`",
        "Plain text/HTML REST endpoints need neither JSON feature",
        "./mvnw liberty:create\n./mvnw liberty:install-feature",
        "./gradlew libertyCreate\n./gradlew libertyInstallFeature",
        "requires that pre-installed assembly",
    ):
        if required_text not in feature_scan:
            errors.append(f"feature scan is missing minimal JSON guidance {required_text!r}")


def validate_links(errors: list[str]) -> None:
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            target = match.group(1).strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, _, anchor = target.partition("#")
            resolved = (path.parent / file_part).resolve() if file_part else path.resolve()
            if not resolved.exists():
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: broken internal link {target}"
                )
                continue
            if anchor and resolved.suffix.lower() == ".md":
                slugs: set[str] = set()
                counts: dict[str, int] = {}
                for heading in MARKDOWN_HEADING.findall(
                    resolved.read_text(encoding="utf-8")
                ):
                    slug = re.sub(r"[^\w\- ]", "", heading.lower())
                    slug = re.sub(r"\s", "-", slug.strip())
                    count = counts.get(slug, 0)
                    counts[slug] = count + 1
                    slugs.add(slug if count == 0 else f"{slug}-{count}")
                if unquote(anchor).lower() not in slugs:
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)}: broken Markdown anchor {target}"
                    )


def fixture_text(root: Path, *, tests: bool | None = None) -> str:
    parts: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "expected.json":
            continue
        is_test = "src/test" in path.as_posix()
        if tests is not None and is_test != tests:
            continue
        try:
            parts.append(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
    return "\n".join(parts)


def classify_fixture(root: Path) -> dict[str, str | bool]:
    main_text = fixture_text(root, tests=False)
    test_text = fixture_text(root, tests=True)
    build_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(root.iterdir())
        if path.is_file()
        and (path.name == "pom.xml" or path.name.startswith("build.gradle"))
    )

    spring_build = "org.springframework" in build_text
    liberty_build = any(
        marker in build_text
        for marker in ("io.openliberty", "jakarta.platform", "liberty-maven-plugin")
    )
    if spring_build and liberty_build:
        build = "PARTIAL"
    elif spring_build:
        build = "PASS"
    else:
        build = "SKIP"

    spring_code = "org.springframework" in main_text
    migrated_code = "import jakarta." in main_text or "Migration required" in main_text
    if spring_code and migrated_code:
        code = "PARTIAL"
    elif spring_code:
        code = "PASS"
    else:
        code = "SKIP"

    view_files = any(
        part in path.as_posix()
        for path in root.rglob("*")
        for part in ("/templates/", "/static/", "/public/")
    )
    server_view_code = any(
        marker in main_text
        for marker in ("@Controller", "ModelAndView", "org.springframework.ui.Model")
    )
    frontend = "PASS" if view_files or server_view_code else "SKIP"

    test_files = [path for path in root.rglob("*") if path.is_file() and "src/test" in path.as_posix()]
    testing = "PASS" if test_files else "SKIP"
    supported_boot_stream = bool(
        re.search(
            r"spring-boot-starter-parent[\s\S]{0,300}<version>[34]\.",
            build_text,
        )
        or re.search(r"org\.springframework\.boot[^\n]*version\s*[=(]?['\"]?[34]\.", build_text)
    )
    spring_bootstrap = (
        "@SpringBootApplication" in main_text or "SpringApplication.run(" in main_text
    )
    security_strategy_required = (
        "spring-boot-starter-security" in build_text
        or any(
            marker in main_text
            for marker in (
                "SecurityFilterChain",
                "@PreAuthorize",
                "@PostAuthorize",
                "oauth2ResourceServer",
                "oauth2Login",
            )
        )
    )
    security_test_evidence = any(
        marker in test_text.lower()
        for marker in ("unauthorized", "forbidden", "csrf", "jwt", "status().is4")
    )
    async_event_strategy_required = any(
        marker in main_text
        for marker in (
            "@Async",
            "ApplicationEventPublisher",
            "@EventListener",
            "@TransactionalEventListener",
            "AsyncConfigurer",
            "TaskExecutor",
            "@Retryable",
            "RetryTemplate",
            "RetryListener",
            "Propagation.",
            "isolation =",
        )
    )
    deployment_artifacts_present = any(
        path.is_file()
        and (
            path.name in {"Dockerfile", "Containerfile", "Chart.yaml", "kustomization.yaml"}
            or path.suffix in {".yaml", ".yml"}
            and any(part in {"k8s", "kubernetes", "deploy", "helm"} for part in path.parts)
        )
        for path in root.rglob("*")
    )
    stack_text = "\n".join((build_text, main_text))
    reactive_strategy_required = any(
        marker in stack_text
        for marker in (
            "spring-boot-starter-webflux",
            "spring-boot-starter-data-r2dbc",
            "org.springframework.web.reactive",
            "reactor.core",
            "ReactiveCrudRepository",
        )
    )
    cloud_strategy_required = any(
        marker in stack_text
        for marker in (
            "org.springframework.cloud",
            "spring-cloud-",
            "@FeignClient",
            "@EnableFeignClients",
        )
    )
    custom_starter_strategy_required = any(
        marker in stack_text
        for marker in (
            "AutoConfiguration.imports",
            "spring.factories",
            "@AutoConfiguration",
            "ImportSelector",
            "BeanFactoryPostProcessor",
            "BeanDefinitionRegistryPostProcessor",
        )
    )
    integration_strategy_required = any(
        marker in stack_text
        for marker in ("spring-integration", "org.springframework.integration", "@IntegrationComponentScan")
    )
    messaging_strategy_required = any(
        marker in stack_text
        for marker in (
            "spring-kafka",
            "spring-boot-starter-amqp",
            "spring-cloud-stream",
            "@KafkaListener",
            "@RabbitListener",
            "JmsTemplate",
            "@JmsListener",
        )
    )
    batch_strategy_required = any(
        marker in stack_text
        for marker in (
            "spring-boot-starter-batch",
            "spring-batch",
            "org.springframework.batch",
            "@Scheduled",
            "org.quartz",
        )
    )
    soap_strategy_required = any(
        marker in stack_text
        for marker in (
            "spring-boot-starter-web-services",
            "spring-ws",
            "org.springframework.ws",
            "@Endpoint",
            "WebServiceTemplate",
        )
    )
    nonrelational_strategy_required = any(
        marker in stack_text
        for marker in (
            "spring-boot-starter-data-redis",
            "spring-boot-starter-data-mongodb",
            "spring-boot-starter-data-elasticsearch",
            "RedisTemplate",
            "MongoTemplate",
            "ElasticsearchOperations",
        )
    )
    external_data_strategy_required = any(
        marker in stack_text
        for marker in (
            "org.postgresql",
            "PGXADataSource",
            "spring.datasource.",
            "flyway",
            "liquibase",
        )
    )
    identity_integration_required = any(
        marker in stack_text
        for marker in (
            "oauth2-resource-server",
            "oauth2-client",
            "oauth2ResourceServer",
            "oauth2Login",
            "issuer-uri",
            "jwk-set-uri",
        )
    )
    observability_strategy_required = any(
        marker in stack_text
        for marker in ("spring-boot-starter-actuator", "micrometer", "opentelemetry")
    )

    return {
        "build": build,
        "code": code,
        "async_event_strategy_required": async_event_strategy_required,
        "deployment_artifacts_present": deployment_artifacts_present,
        "security_strategy_required": security_strategy_required,
        "security_test_gap": security_strategy_required and not security_test_evidence,
        "frontend": frontend,
        "testing": testing,
        "coverage_risk": not bool(test_files),
        "repository_strategy_required": any(
            marker in main_text
            for marker in (
                "org.springframework.data.repository",
                "org.springframework.data.jpa.repository",
            )
        ),
        "rehost_candidate": supported_boot_stream and spring_bootstrap,
        "complex_stack_strategy_required": any(
            (
                reactive_strategy_required,
                cloud_strategy_required,
                custom_starter_strategy_required,
                integration_strategy_required,
                messaging_strategy_required,
                batch_strategy_required,
                soap_strategy_required,
                nonrelational_strategy_required,
            )
        ),
        "reactive_strategy_required": reactive_strategy_required,
        "cloud_strategy_required": cloud_strategy_required,
        "integration_strategy_required": integration_strategy_required,
        "custom_starter_strategy_required": custom_starter_strategy_required,
        "messaging_strategy_required": messaging_strategy_required,
        "batch_strategy_required": batch_strategy_required,
        "soap_strategy_required": soap_strategy_required,
        "nonrelational_strategy_required": nonrelational_strategy_required,
        "external_data_strategy_required": external_data_strategy_required,
        "identity_integration_required": identity_integration_required,
        "observability_strategy_required": observability_strategy_required,
    }


def validate_fixtures(errors: list[str]) -> None:
    if not FIXTURES_ROOT.is_dir():
        errors.append("tests/fixtures: evaluation fixtures are missing")
        return
    fixtures = sorted(path for path in FIXTURES_ROOT.iterdir() if path.is_dir())
    if len(fixtures) < 16:
        errors.append("tests/fixtures: expected at least sixteen representative scenarios")
    covered_fields: set[str] = set()
    for fixture in fixtures:
        expected_path = fixture / "expected.json"
        if not expected_path.is_file():
            errors.append(f"{fixture.relative_to(REPO_ROOT)}: missing expected.json")
            continue
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        actual = classify_fixture(fixture)
        covered_fields.update(expected)
        mismatches = {
            key: {"expected": value, "actual": actual.get(key)}
            for key, value in expected.items()
            if actual.get(key) != value
        }
        unknown = set(expected) - set(actual)
        if mismatches or unknown:
            errors.append(
                f"{fixture.relative_to(REPO_ROOT)}: gate classification mismatch; "
                f"mismatches {mismatches}, unknown fields {sorted(unknown)}"
            )
    missing_coverage = set(classify_fixture(fixtures[0])) - covered_fields if fixtures else set()
    if missing_coverage:
        errors.append(
            "tests/fixtures: classifier fields lack explicit expected coverage: "
            + ", ".join(sorted(missing_coverage))
        )


def validate_e2e(errors: list[str]) -> None:
    manifest = E2E_ROOT / "scenarios.json"
    runner = SKILL_ROOT / "scripts" / "run_e2e.py"
    if not manifest.is_file() or not runner.is_file():
        errors.append("tests/e2e: golden manifest and runner are required")
        return
    data = json.loads(manifest.read_text(encoding="utf-8"))
    scenarios = data.get("scenarios", [])
    names = {scenario.get("name") for scenario in scenarios}
    required = {
        "maven-security-events",
        "gradle-data-frontend",
        "partial-resume",
        "maven-rehost-boot3",
        "gradle-rehost-boot4",
    }
    if data.get("schema_version") != 1 or not required.issubset(names):
        errors.append("tests/e2e: required Maven, Gradle, and partial-resume scenarios are missing")
    workflow = REPO_ROOT / ".github" / "workflows" / "compatibility.yml"
    if not workflow.is_file():
        errors.append("online compatibility workflow is missing")
    else:
        workflow_text = workflow.read_text(encoding="utf-8")
        for required_text in (
            "schedule:",
            "workflow_dispatch:",
            "java: [\"17\", \"21\", \"25\"]",
            "--mode build",
            "--mode runtime",
            "run_agent_eval.py --mode static",
            "run_production_evals.py --mode static",
            "run_integration_lab.py --mode static",
        ):
            if required_text not in workflow_text:
                errors.append(f"compatibility workflow is missing {required_text!r}")


def validate_evaluation_harnesses(errors: list[str]) -> None:
    agent_manifest = AGENT_EVAL_ROOT / "scenarios.json"
    agent_runner = SKILL_ROOT / "scripts" / "run_agent_eval.py"
    if not agent_manifest.is_file() or not agent_runner.is_file():
        errors.append("tests/agent-evals: manifest and agent-in-the-loop runner are required")
    else:
        data = json.loads(agent_manifest.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or len(data.get("scenarios", [])) < 10:
            errors.append("tests/agent-evals: at least ten versioned scenarios are required")
        for scenario in data.get("scenarios", []):
            for key in ("name", "source", "prompt", "required_paths", "required_text", "build"):
                if key not in scenario:
                    errors.append(f"tests/agent-evals: scenario is missing {key!r}")

    production_manifest = PRODUCTION_ROOT / "scenarios.json"
    production_runner = SKILL_ROOT / "scripts" / "run_production_evals.py"
    if not production_manifest.is_file() or not production_runner.is_file():
        errors.append("tests/production: manifest and integration evidence runner are required")
    else:
        data = json.loads(production_manifest.read_text(encoding="utf-8"))
        scenarios = data.get("scenarios", [])
        if data.get("schema_version") != 1 or len(scenarios) < 3:
            errors.append("tests/production: at least three versioned integration scenarios are required")
        for scenario in scenarios:
            if len(scenario.get("failure_cases", [])) < 3:
                errors.append(
                    f"tests/production: {scenario.get('name', '<unnamed>')} needs at least three failure cases"
                )

    lab_manifest = INTEGRATION_LAB_ROOT / "scenarios.json"
    lab_runner = SKILL_ROOT / "scripts" / "run_integration_lab.py"
    if not lab_manifest.is_file() or not lab_runner.is_file():
        errors.append("tests/integration-lab: manifest and disposable lab runner are required")
    else:
        data = json.loads(lab_manifest.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or len(data.get("scenarios", [])) < 3:
            errors.append("tests/integration-lab: at least three versioned scenarios are required")
        lab_text = lab_runner.read_text(encoding="utf-8")
        compose_text = (INTEGRATION_LAB_ROOT / "compose.yaml").read_text(encoding="utf-8")
        for required_text in (
            "--confirm-disposable",
            "--test-command-json",
            "COMPOSE_PROJECT_NAME",
            '"down", "--volumes"',
        ):
            if required_text not in lab_text:
                errors.append(f"disposable lab runner is missing {required_text!r}")
        for required_text in ("LAB_KAFKA_PORT", "EXTERNAL://127.0.0.1:"):
            if required_text not in compose_text:
                errors.append(f"disposable lab compose is missing {required_text!r}")

    required_tools = {
        "analyze_project.py",
        "generate_characterization.py",
        "generate_liberty_config.py",
        "safe_codemods.py",
        "verify_parity.py",
        "run_integration_lab.py",
    }
    missing_tools = sorted(
        name for name in required_tools if not (SKILL_ROOT / "scripts" / name).is_file()
    )
    if missing_tools:
        errors.append(f"deterministic migration tools are missing {missing_tools}")
    else:
        codemod = (SKILL_ROOT / "scripts" / "safe_codemods.py").read_text(encoding="utf-8")
        for required_text in (
            "javax.annotation.processing",
            "javax.transaction.xa",
            "javax.sql",
            "javax.cache",
            "--confirm-apply",
        ):
            if required_text not in codemod:
                errors.append(f"safe codemod is missing protected boundary {required_text!r}")
    if not (TOOLING_ROOT / "test_tooling.py").is_file():
        errors.append("tests/tooling/test_tooling.py is required")

    validate_workflow = REPO_ROOT / ".github" / "workflows" / "validate.yml"
    if validate_workflow.is_file():
        workflow_text = validate_workflow.read_text(encoding="utf-8")
        for required_text in ("test_tooling.py", "run_integration_lab.py --mode static"):
            if required_text not in workflow_text:
                errors.append(f"validate workflow is missing {required_text!r}")


def main() -> int:
    errors: list[str] = []
    validate_frontmatter(errors)
    validate_invariants(errors)
    validate_links(errors)
    validate_fixtures(errors)
    validate_e2e(errors)
    validate_evaluation_harnesses(errors)

    if errors:
        print("Skill validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Skill validation passed: {len(markdown_files())} Markdown files and "
        f"{len(list(FIXTURES_ROOT.iterdir()))} fixtures checked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
