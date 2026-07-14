#!/usr/bin/env python3
"""Validate or start the disposable complex-migration integration lab."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LAB_ROOT = REPO_ROOT / "tests" / "integration-lab"
LAB_MANIFEST = LAB_ROOT / "scenarios.json"
PRODUCTION_MANIFEST = REPO_ROOT / "tests" / "production" / "scenarios.json"
COMPOSE = LAB_ROOT / "compose.yaml"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> list[str]:
    errors: list[str] = []
    for path in (LAB_MANIFEST, PRODUCTION_MANIFEST, COMPOSE, LAB_ROOT / "otel-collector.yaml"):
        if not path.is_file():
            errors.append(f"missing integration-lab file: {path.relative_to(REPO_ROOT)}")
    if errors:
        return errors
    lab = load(LAB_MANIFEST)
    production = load(PRODUCTION_MANIFEST)
    if lab.get("schema_version") != 1:
        errors.append("integration lab manifest must use schema_version 1")
    lab_scenarios = {item.get("name"): item for item in lab.get("scenarios", [])}
    production_names = {item.get("name") for item in production.get("scenarios", [])}
    if set(lab_scenarios) != production_names:
        errors.append("integration lab scenarios must cover every production scenario exactly")
    allowed_services = {"postgres", "kafka", "keycloak", "otel-collector"}
    for name, scenario in lab_scenarios.items():
        services = scenario.get("services")
        if not isinstance(services, list) or not services or not set(services) <= allowed_services:
            errors.append(f"{name}: invalid disposable services")
        smoke = scenario.get("smoke")
        if smoke is not None and (
            not isinstance(smoke, list) or len(smoke) < 2 or smoke[0] not in services
        ):
            errors.append(f"{name}: smoke must start with one of its services")
        for probe in scenario.get("probes", []):
            if (
                not isinstance(probe, dict)
                or probe.get("service") not in services
                or not isinstance(probe.get("port"), int)
                or not isinstance(probe.get("path"), str)
                or not probe["path"].startswith("/")
            ):
                errors.append(f"{name}: invalid HTTP probe {probe!r}")
        endpoint_names: set[str] = set()
        for endpoint in scenario.get("endpoints", []):
            if (
                not isinstance(endpoint, dict)
                or endpoint.get("service") not in services
                or not isinstance(endpoint.get("port"), int)
                or not isinstance(endpoint.get("environment"), str)
                or not endpoint["environment"].startswith("LAB_")
                or not isinstance(endpoint.get("template"), str)
                or "{port}" not in endpoint["template"]
                or endpoint["environment"] in endpoint_names
            ):
                errors.append(f"{name}: invalid or duplicate endpoint {endpoint!r}")
            else:
                endpoint_names.add(endpoint["environment"])
    compose_text = COMPOSE.read_text(encoding="utf-8")
    if ":latest" in compose_text:
        errors.append("integration lab images must use pinned tags")
    if "network_mode: host" in compose_text:
        errors.append("integration lab must not use the host network")
    for variable in (
        "LAB_POSTGRES_PASSWORD",
        "LAB_KEYCLOAK_ADMIN_PASSWORD",
        "LAB_KAFKA_PORT",
    ):
        if variable not in compose_text:
            errors.append(f"integration lab must externalize {variable}")
    return errors


def compose_command(project: str, *args: str) -> list[str]:
    return ["docker", "compose", "-p", project, "-f", str(COMPOSE), *args]


def lab_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.setdefault("LAB_POSTGRES_PASSWORD", secrets.token_urlsafe(24))
    environment.setdefault("LAB_KEYCLOAK_ADMIN", "migration-admin")
    environment.setdefault("LAB_KEYCLOAK_ADMIN_PASSWORD", secrets.token_urlsafe(24))
    if "LAB_KAFKA_PORT" not in environment:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            environment["LAB_KAFKA_PORT"] = str(listener.getsockname()[1])
    environment.setdefault("LAB_POSTGRES_USER", "liberty")
    environment.setdefault("LAB_POSTGRES_DATABASE", "liberty")
    return environment


def wait_for_services(project: str, services: list[str], environment: dict[str, str], timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = subprocess.run(
            compose_command(project, "ps", "--status", "running", "--services"),
            cwd=LAB_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        running = set(result.stdout.splitlines())
        if set(services) <= running:
            return
        time.sleep(2)
    raise RuntimeError(f"timed out waiting for services: {', '.join(services)}")


def retry_smoke(
    project: str,
    smoke: list[str],
    environment: dict[str, str],
    timeout: int,
) -> str:
    service, *command = smoke
    deadline = time.monotonic() + timeout
    last_output = "not attempted"
    while time.monotonic() < deadline:
        result = subprocess.run(
            compose_command(project, "exec", "-T", service, *command),
            cwd=LAB_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        last_output = result.stdout
        if result.returncode == 0:
            return result.stdout
        time.sleep(2)
    raise RuntimeError(f"service smoke timed out for {service}: {last_output[-300:]}")


def wait_http_probe(
    project: str,
    probe: dict,
    environment: dict[str, str],
    timeout: int,
) -> str:
    mapping = published_port(project, probe["service"], probe["port"], environment)
    url = f"http://{mapping}{probe['path']}"
    deadline = time.monotonic() + timeout
    last_error = "not attempted"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                body = response.read().decode("utf-8", errors="replace")
                if response.status == 200:
                    return f"{url} -> {response.status}\n{body[:500]}"
                last_error = f"HTTP {response.status}"
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = str(exc)
        time.sleep(2)
    raise RuntimeError(f"HTTP probe timed out for {url}: {last_error}")


def published_port(
    project: str,
    service: str,
    port: int,
    environment: dict[str, str],
) -> str:
    return subprocess.run(
        compose_command(project, "port", service, str(port)),
        cwd=LAB_ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    ).stdout.strip()


def resolve_endpoints(
    project: str,
    endpoints: list[dict],
    environment: dict[str, str],
) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for endpoint in endpoints:
        mapping = published_port(project, endpoint["service"], endpoint["port"], environment)
        host_port = mapping.rsplit(":", 1)[-1]
        resolved[endpoint["environment"]] = endpoint["template"].format(port=host_port)
    return resolved


def run_scenario(
    name: str,
    evidence_root: Path,
    timeout: int,
    test_command: list[str] | None,
    test_cwd: Path,
) -> None:
    manifest = load(LAB_MANIFEST)
    scenario = next((item for item in manifest["scenarios"] if item["name"] == name), None)
    if scenario is None:
        raise ValueError(f"unknown integration-lab scenario: {name}")
    project = f"liberty-migration-{secrets.token_hex(4)}"
    environment = lab_environment()
    environment["COMPOSE_PROJECT_NAME"] = project
    environment["COMPOSE_FILE"] = str(COMPOSE)
    evidence_root.mkdir(parents=True, exist_ok=True)
    log_path = evidence_root / f"{name}-lab.log"
    output: list[str] = []
    try:
        up = subprocess.run(
            compose_command(project, "up", "-d", *scenario["services"]),
            cwd=LAB_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )
        output.append(up.stdout)
        wait_for_services(project, scenario["services"], environment, timeout)
        if scenario.get("smoke"):
            output.append(retry_smoke(project, scenario["smoke"], environment, timeout))
        for probe in scenario.get("probes", []):
            output.append(wait_http_probe(project, probe, environment, timeout))
        endpoints = resolve_endpoints(project, scenario.get("endpoints", []), environment)
        environment.update(endpoints)
        output.append("resolved non-secret endpoints:\n" + json.dumps(endpoints, indent=2, sort_keys=True))
        if test_command:
            test = subprocess.run(
                test_command,
                cwd=test_cwd,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True,
                timeout=timeout,
            )
            output.append(test.stdout)
    except (OSError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        try:
            logs = subprocess.run(
                compose_command(project, "logs", "--no-color"),
                cwd=LAB_ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            output.append(logs.stdout)
        except OSError as log_error:
            output.append(f"could not capture compose logs: {log_error}")
        raise
    finally:
        try:
            subprocess.run(
                compose_command(project, "down", "--volumes", "--remove-orphans"),
                cwd=LAB_ROOT,
                env=environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError:
            pass
        log_path.write_text("\n".join(output), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("static", "run"), default="static")
    parser.add_argument("--scenario")
    parser.add_argument("--confirm-disposable", action="store_true")
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--test-command-json")
    parser.add_argument("--test-cwd", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = validate()
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if args.mode == "static":
        print(f"Disposable integration lab passed for {len(load(LAB_MANIFEST)['scenarios'])} scenarios.")
        return 0
    if not args.confirm_disposable:
        parser.error("run mode requires --confirm-disposable")
    if not args.scenario or args.evidence_root is None:
        parser.error("run mode requires --scenario and --evidence-root")
    test_command = None
    if args.test_command_json:
        try:
            test_command = json.loads(args.test_command_json)
        except json.JSONDecodeError as exc:
            parser.error(f"--test-command-json is invalid JSON: {exc}")
        if not isinstance(test_command, list) or not test_command or not all(
            isinstance(item, str) and item for item in test_command
        ):
            parser.error("--test-command-json must be a non-empty JSON string array")
    if not args.test_cwd.is_dir():
        parser.error(f"--test-cwd is not a directory: {args.test_cwd}")
    try:
        run_scenario(
            args.scenario,
            args.evidence_root,
            args.timeout,
            test_command,
            args.test_cwd,
        )
    except (
        OSError,
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    action = "test command passed" if test_command else "services smoke-checked"
    print(f"Disposable integration lab {action} and cleaned up: {args.scenario}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
