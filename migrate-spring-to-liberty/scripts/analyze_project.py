#!/usr/bin/env python3
"""Create a deterministic Spring-to-Liberty migration inventory."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


IGNORED_PARTS = {
    ".git",
    ".gradle",
    ".idea",
    ".mvn",
    ".settings",
    "build",
    "node_modules",
    "out",
    "target",
}
TEXT_SUFFIXES = {
    ".conf",
    ".gradle",
    ".graphql",
    ".groovy",
    ".html",
    ".java",
    ".jsp",
    ".json",
    ".kt",
    ".kts",
    ".properties",
    ".proto",
    ".sql",
    ".toml",
    ".txt",
    ".wsdl",
    ".xhtml",
    ".xml",
    ".xsd",
    ".yaml",
    ".yml",
}
TEXT_NAMES = {
    "AutoConfiguration.imports",
    "Dockerfile",
    "Containerfile",
    "gradlew",
    "mvnw",
    "settings.gradle",
    "settings.gradle.kts",
    "spring.factories",
}


@dataclass(frozen=True)
class CapabilityDefinition:
    identifier: str
    adapter: str
    risk: str
    default_route: str
    markers: tuple[str, ...]


CAPABILITIES = (
    CapabilityDefinition(
        "web-api",
        "modules/code.md",
        "medium",
        "rewrite-or-rehost",
        (
            "@RestController",
            "@RequestMapping",
            "@GetMapping",
            "@PostMapping",
            "org.springframework.web.bind.annotation",
        ),
    ),
    CapabilityDefinition(
        "frontend",
        "modules/frontend.md",
        "medium",
        "contract-selected-view",
        (
            "thymeleaf",
            "ModelAndView",
            "org.springframework.ui.Model",
            "@Controller",
            "@ModelAttribute",
            "BindingResult",
            "@InitBinder",
            "WebDataBinder",
            "th:field",
            "th:errors",
            "#fields",
            "<form:form",
            "<form:input",
            "<spring:bind",
        ),
    ),
    CapabilityDefinition(
        "repositories",
        "references/jakarta-data.md",
        "high",
        "jakarta-data-entitymanager-or-staged",
        ("JpaRepository", "CrudRepository", "spring-data-jpa", "spring-data-jdbc"),
    ),
    CapabilityDefinition(
        "security",
        "modules/security.md",
        "critical",
        "dedicated-module",
        (
            "spring-boot-starter-security",
            "SecurityFilterChain",
            "@PreAuthorize",
            "oauth2ResourceServer",
            "oauth2Login",
            "spring.security.",
        ),
    ),
    CapabilityDefinition(
        "async-events",
        "modules/async-events.md",
        "high",
        "dedicated-module",
        (
            "@Async",
            "ApplicationEventPublisher",
            "@EventListener",
            "@TransactionalEventListener",
            "@Retryable",
            "RetryTemplate",
            "Propagation.",
        ),
    ),
    CapabilityDefinition(
        "messaging",
        "modules/messaging.md",
        "critical",
        "dedicated-module",
        (
            "spring-kafka",
            "@KafkaListener",
            "spring-boot-starter-amqp",
            "@RabbitListener",
            "@JmsListener",
            "JmsTemplate",
            "spring-pulsar",
            "@PulsarListener",
            "spring-cloud-stream",
            "spring-integration",
        ),
    ),
    CapabilityDefinition(
        "batch-scheduling",
        "modules/batch-scheduling.md",
        "high",
        "dedicated-module",
        (
            "spring-batch",
            "@EnableBatchProcessing",
            "@Scheduled",
            "org.quartz",
            "TaskScheduler",
        ),
    ),
    CapabilityDefinition(
        "data-xa-schema",
        "modules/data-xa-schema.md",
        "critical",
        "dedicated-module",
        (
            "spring.datasource.",
            "spring.jpa.",
            "spring-boot-starter-jdbc",
            "jdbc:",
            "org.postgresql",
            "mysql-connector",
            "db2jcc",
            "oracle.jdbc",
            "mssql-jdbc",
            "PGXADataSource",
            "XADataSource",
            "flyway",
            "liquibase",
            "ChainedTransactionManager",
        ),
    ),
    CapabilityDefinition(
        "identity-observability",
        "modules/identity-observability.md",
        "critical",
        "dedicated-module",
        (
            "oauth2-resource-server",
            "oauth2Login",
            "issuer-uri",
            "jwk-set-uri",
            "spring-boot-starter-actuator",
            "micrometer",
            "opentelemetry",
        ),
    ),
    CapabilityDefinition(
        "reactive-cloud",
        "modules/reactive-cloud.md",
        "critical",
        "staged-retention-or-redesign",
        (
            "spring-boot-starter-webflux",
            "spring-boot-starter-data-r2dbc",
            "reactor.core",
            "ReactiveCrudRepository",
            "org.springframework.cloud",
            "@FeignClient",
            "spring-cloud-gateway",
        ),
    ),
    CapabilityDefinition(
        "soap-nonrelational",
        "modules/soap-nonrelational.md",
        "critical",
        "retain-client-redesign-or-staged",
        (
            "spring-boot-starter-web-services",
            "org.springframework.ws",
            "graphql",
            "io.grpc",
            "RedisTemplate",
            "MongoTemplate",
            "ElasticsearchOperations",
            "spring-boot-starter-data-redis",
            "spring-boot-starter-data-mongodb",
        ),
    ),
    CapabilityDefinition(
        "custom-spring-runtime",
        "modules/reactive-cloud.md",
        "critical",
        "staged-retention-or-project-specific-design",
        (
            "AutoConfiguration.imports",
            "spring.factories",
            "@AutoConfiguration",
            "ImportSelector",
            "BeanFactoryPostProcessor",
            "BeanDefinitionRegistryPostProcessor",
        ),
    ),
    CapabilityDefinition(
        "deployment",
        "modules/deploy.md",
        "high",
        "preserve-and-validate",
        ("Dockerfile", "Containerfile", "kind: Deployment", "Chart.yaml", "kustomization.yaml"),
    ),
)


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.relative_to(root).parts):
            continue
        if (
            path.suffix.lower() in TEXT_SUFFIXES
            or path.name in TEXT_NAMES
            or path.name.endswith("AutoConfiguration.imports")
        ):
            files.append(path)
    return sorted(files)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def evidence_for(root: Path, files: list[Path], markers: tuple[str, ...]) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for path in files:
        text = read_text(path)
        searchable = f"{path.name}\n{text}"
        for marker in markers:
            if marker.lower() in searchable.lower():
                evidence.append({"path": path.relative_to(root).as_posix(), "marker": marker})
    return evidence[:25]


def build_inventory(root: Path, files: list[Path]) -> dict:
    poms = [path for path in files if path.name == "pom.xml"]
    gradle_builds = [
        path for path in files if path.name in {"build.gradle", "build.gradle.kts"}
    ]
    settings = [
        path for path in files if path.name in {"settings.gradle", "settings.gradle.kts"}
    ]
    systems = []
    if poms:
        systems.append("maven")
    if gradle_builds:
        systems.append("gradle")

    launchers = []
    if (root / "mvnw").is_file():
        launchers.append("./mvnw")
    elif poms:
        launchers.append("mvn")
    if (root / "gradlew").is_file():
        launchers.append("./gradlew")
    elif gradle_builds:
        launchers.append("gradle")

    modules: list[dict] = []
    module_names: set[str] = set()
    for pom in poms:
        text = read_text(pom)
        declared = re.findall(r"<module>\s*([^<]+?)\s*</module>", text)
        artifact_match = re.search(r"<artifactId>\s*([^<]+?)\s*</artifactId>", text)
        modules.append(
            {
                "build_file": pom.relative_to(root).as_posix(),
                "artifact": artifact_match.group(1) if artifact_match else pom.parent.name,
                "declared_modules": sorted(set(declared)),
            }
        )
        module_names.update(declared)
    for setting in settings:
        text = read_text(setting)
        for match in re.findall(r"(?:include|includeFlat)\s*\(?([^\n]+)", text):
            module_names.update(re.findall(r"['\"]:?(.*?)['\"]", match))

    return {
        "systems": systems,
        "launchers": launchers,
        "build_files": [path.relative_to(root).as_posix() for path in poms + gradle_builds],
        "multi_module": len(poms) + len(gradle_builds) > 1 or bool(module_names),
        "modules": modules,
        "declared_module_names": sorted(name for name in module_names if name),
    }


def spring_inventory(root: Path, files: list[Path]) -> dict:
    combined = "\n".join(read_text(path) for path in files)
    versions: set[str] = set()
    patterns = (
        r"spring-boot-starter-parent[\s\S]{0,350}?<version>\s*([^<\s]+)",
        r"org\.springframework\.boot['\"]?\)?\s+version\s+['\"]([^'\"]+)",
        r"id\(['\"]org\.springframework\.boot['\"]\)\s+version\s+['\"]([^'\"]+)",
    )
    for pattern in patterns:
        versions.update(re.findall(pattern, combined, flags=re.IGNORECASE))
    streams = sorted({version.split(".", 1)[0] for version in versions if version[:1].isdigit()})
    java_files = [path for path in files if path.suffix == ".java"]
    test_files = [
        path
        for path in files
        if "/src/test/" in f"/{path.relative_to(root).as_posix()}"
    ]
    imports = sorted(set(re.findall(r"import\s+(org\.springframework\.[\w.*]+);", combined)))
    return {
        "detected": "org.springframework" in combined or "spring-boot" in combined,
        "boot_versions": sorted(versions),
        "boot_streams": streams,
        "rehost_eligible_stream": bool(streams) and all(stream in {"3", "4"} for stream in streams),
        "bootstrap_present": "@SpringBootApplication" in combined or "SpringApplication.run(" in combined,
        "spring_imports": imports,
        "spring_import_count": sum(read_text(path).count("import org.springframework") for path in java_files),
        "java_source_count": len(java_files),
        "test_source_count": len(test_files),
    }


def recommend_route(spring: dict, capabilities: list[dict], build: dict) -> dict:
    critical = [item["id"] for item in capabilities if item["risk"] == "critical"]
    if not spring["detected"]:
        route = "not-a-spring-migration"
        reason = "No Spring build or source markers were detected."
    elif not spring["bootstrap_present"]:
        route = "rewrite-or-staged-library-migration"
        reason = "Spring is present without an executable Spring Boot bootstrap."
    elif critical and spring["rehost_eligible_stream"]:
        route = "rehost-first-then-staged-slices"
        reason = "A supported Boot stream and critical semantic stacks were detected."
    elif critical:
        route = "upgrade-or-staged-redesign"
        reason = "Critical semantic stacks are present and the Boot stream is not directly rehost eligible."
    elif spring["rehost_eligible_stream"]:
        route = "choose-rehost-or-complete-rewrite"
        reason = "The application is eligible for Liberty rehosting and has no detected critical stack."
    else:
        route = "staged-rewrite"
        reason = "The application is not directly eligible for the supported Boot 3/4 rehost route."
    blockers = []
    if build["multi_module"]:
        blockers.append("Confirm migration boundaries and build order for every module.")
    if spring["test_source_count"] == 0 and spring["detected"]:
        blockers.append("Create characterization coverage before changing production code.")
    blockers.extend(
        f"Select and confirm the {item['adapter']} route for {item['id']}."
        for item in capabilities
        if item["risk"] == "critical"
    )
    return {"route": route, "reason": reason, "blockers": blockers}


def analyze(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"project root is not a directory: {root}")
    files = iter_text_files(root)
    build = build_inventory(root, files)
    spring = spring_inventory(root, files)
    capabilities = []
    for definition in CAPABILITIES:
        evidence = evidence_for(root, files, definition.markers)
        if evidence:
            capabilities.append(
                {
                    "id": definition.identifier,
                    "adapter": definition.adapter,
                    "risk": definition.risk,
                    "default_route": definition.default_route,
                    "evidence": evidence,
                }
            )
    capabilities.sort(key=lambda item: item["id"])
    recommendation = recommend_route(spring, capabilities, build)
    return {
        "schema_version": 1,
        "project": root.name,
        "build": build,
        "spring": spring,
        "capabilities": capabilities,
        "recommended_migration": recommendation,
        "required_adapters": sorted({item["adapter"] for item in capabilities}),
        "suggested_artifacts": [
            "migration-inventory.json",
            "migration-characterization.json",
            "migration-report.md",
        ],
    }


def render_markdown(inventory: dict) -> str:
    lines = [
        f"# Migration Inventory: {inventory['project']}",
        "",
        f"- Recommended route: `{inventory['recommended_migration']['route']}`",
        f"- Reason: {inventory['recommended_migration']['reason']}",
        f"- Build systems: {', '.join(inventory['build']['systems']) or 'none detected'}",
        f"- Multi-module: {'yes' if inventory['build']['multi_module'] else 'no'}",
        f"- Spring Boot versions: {', '.join(inventory['spring']['boot_versions']) or 'unknown'}",
        f"- Java sources/tests: {inventory['spring']['java_source_count']}/{inventory['spring']['test_source_count']}",
        "",
        "## Detected capabilities",
        "",
        "| Capability | Risk | Adapter | Evidence |",
        "|---|---|---|---|",
    ]
    for item in inventory["capabilities"]:
        evidence = ", ".join(entry["path"] for entry in item["evidence"][:3])
        lines.append(f"| {item['id']} | {item['risk']} | `{item['adapter']}` | {evidence} |")
    if not inventory["capabilities"]:
        lines.append("| none | — | — | — |")
    lines.extend(["", "## Required decisions", ""])
    blockers = inventory["recommended_migration"]["blockers"]
    lines.extend(f"- [ ] {blocker}" for blocker in blockers)
    if not blockers:
        lines.append("- None detected.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        inventory = analyze(args.project)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    content = (
        json.dumps(inventory, indent=2, sort_keys=True) + "\n"
        if args.format == "json"
        else render_markdown(inventory)
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
