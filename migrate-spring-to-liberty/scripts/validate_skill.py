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

INVALID_TEXT = {
    "<feature>beanValidation-3.1</feature>": "Jakarta EE 11 uses validation-3.1",
    "<feature>appSecurity-5.0</feature>": "Jakarta EE 11 uses appSecurity-6.0",
    "<feature>ejbLite-4.0</feature>": "use enterpriseBeansLite-4.0",
    "<feature>ejb-4.0</feature>": "use enterpriseBeans-4.0",
    "<feature>messaging-3.0</feature>": "Jakarta EE 11 uses messaging-3.1",
    "<feature>servlet-6.0</feature>": "Jakarta EE 11 uses servlet-6.1",
    "<feature>concurrent-3.0</feature>": "Jakarta EE 11 uses concurrent-3.1",
    "io.openliberty.tools:microshed-testing-liberty": "MicroShed uses org.microshed",
    "quarkus-rest": "Quarkus artifacts do not belong in a Liberty mapping",
    "@IfBuildProfile": "not a portable CDI or MicroProfile annotation",
    "@LookupIfProperty": "not a portable CDI or MicroProfile annotation",
    "MicroProfile Scheduler (`mpScheduler`)": "there is no mpScheduler feature",
    "Jakarta EE 11 mandates Java 21": "Jakarta EE 11 has a Java 17 minimum",
    "have no direct Jakarta EE equivalent": "Jakarta EE 11 includes Jakarta Data 1.0",
    "Remove Spring CSRF tokens from HTML and JavaScript": "replace and test CSRF protection first",
    "LibertyServerContainerConfiguration": "MicroShed documents SharedContainerConfiguration with ApplicationContainer",
    "new LibertyServerContainer(": "MicroShed documents ApplicationContainer",
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
    "cdi-4.1",
    "dataContainer-1.0",
    "faces-4.1",
    "jakartaee-11.0",
    "jsonb-3.0",
    "jsonp-2.1",
    "messaging-3.1",
    "microProfile-7.0",
    "mpConfig-3.1",
    "mpHealth-4.0",
    "mpFaultTolerance-4.1",
    "mpJwt-2.1",
    "openidConnectClient-1.0",
    "mpMetrics-5.1",
    "mpOpenAPI-4.0",
    "pages-4.0",
    "persistence-3.2",
    "restfulWS-4.0",
    "servlet-6.1",
    "springBoot-3.0",
    "springBoot-4.0",
    "validation-3.1",
    "webProfile-11.0",
    "wmqJmsClient-3.0",
    "xmlBinding-4.0",
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
    }


def validate_fixtures(errors: list[str]) -> None:
    if not FIXTURES_ROOT.is_dir():
        errors.append("tests/fixtures: evaluation fixtures are missing")
        return
    fixtures = sorted(path for path in FIXTURES_ROOT.iterdir() if path.is_dir())
    if len(fixtures) < 8:
        errors.append("tests/fixtures: expected at least eight representative scenarios")
    for fixture in fixtures:
        expected_path = fixture / "expected.json"
        if not expected_path.is_file():
            errors.append(f"{fixture.relative_to(REPO_ROOT)}: missing expected.json")
            continue
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        actual = classify_fixture(fixture)
        if actual != expected:
            errors.append(
                f"{fixture.relative_to(REPO_ROOT)}: gate classification mismatch; "
                f"expected {expected}, got {actual}"
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
    required = {"maven-security-events", "gradle-data-frontend", "partial-resume"}
    if data.get("schema_version") != 1 or not required.issubset(names):
        errors.append("tests/e2e: required Maven, Gradle, and partial-resume scenarios are missing")
    workflow = REPO_ROOT / ".github" / "workflows" / "compatibility.yml"
    if not workflow.is_file():
        errors.append("online compatibility workflow is missing")
    else:
        workflow_text = workflow.read_text(encoding="utf-8")
        for required_text in ("schedule:", "workflow_dispatch:", "--mode build", "--mode runtime"):
            if required_text not in workflow_text:
                errors.append(f"compatibility workflow is missing {required_text!r}")


def main() -> int:
    errors: list[str] = []
    validate_frontmatter(errors)
    validate_invariants(errors)
    validate_links(errors)
    validate_fixtures(errors)
    validate_e2e(errors)
    if not (REPO_ROOT / "LICENSE").is_file():
        errors.append("repository is missing LICENSE")

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
