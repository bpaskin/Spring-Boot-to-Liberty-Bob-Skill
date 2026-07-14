#!/usr/bin/env python3
"""Validate and optionally execute golden before/after migration scenarios."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
E2E_ROOT = REPO_ROOT / "tests" / "e2e"
MANIFEST = E2E_ROOT / "scenarios.json"


def tree_text(root: Path) -> str:
    parts: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in {"build", "target", ".gradle"} for part in path.parts):
            continue
        try:
            parts.append(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
    return "\n".join(parts)


def load_scenarios() -> list[dict]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("scenarios"), list):
        raise ValueError("tests/e2e/scenarios.json has an unsupported schema")
    return data["scenarios"]


def validate_scenario(scenario: dict) -> list[str]:
    errors: list[str] = []
    name = scenario.get("name", "<unnamed>")
    before = E2E_ROOT / scenario.get("before", "")
    after = E2E_ROOT / scenario.get("after", "")
    if not before.is_dir() or not after.is_dir():
        return [f"{name}: before/after directories must exist"]
    before_text = tree_text(before)
    after_text = tree_text(after)
    if "org.springframework" not in before_text:
        errors.append(f"{name}: before fixture does not contain Spring code")
    if not scenario.get("allow_spring_after") and "org.springframework" in after_text:
        errors.append(f"{name}: complete after fixture still contains Spring code")
    for marker in scenario.get("required_after", []):
        if marker not in after_text:
            errors.append(f"{name}: after fixture is missing required marker {marker!r}")
    for marker in scenario.get("forbidden_after", []):
        if marker in after_text:
            errors.append(f"{name}: after fixture contains forbidden marker {marker!r}")
    for phase in ("build", "compatibility"):
        for command in scenario.get(phase, []):
            if not isinstance(command, list) or not command or not all(isinstance(arg, str) for arg in command):
                errors.append(f"{name}: {phase} commands must be non-empty argument arrays")
    runtime = scenario.get("runtime")
    if runtime:
        for field in ("start", "stop"):
            command = runtime.get(field)
            if not isinstance(command, list) or not command or not all(isinstance(arg, str) for arg in command):
                errors.append(f"{name}: runtime {field} must be a non-empty argument array")
        probes = runtime.get("probes")
        if not isinstance(probes, list) or not probes:
            errors.append(f"{name}: runtime must define at least one probe")
        else:
            for probe in probes:
                if not isinstance(probe, dict) or not probe.get("url") or not isinstance(probe.get("status", 200), int):
                    errors.append(f"{name}: each runtime probe needs a URL and integer status")
    return errors


def run_command(command: list[str], cwd: Path) -> None:
    print(f"[{cwd.name}] $ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def run_runtime(runtime: dict, cwd: Path) -> None:
    stop = runtime["stop"]
    try:
        run_command(runtime["start"], cwd)
        for probe in runtime["probes"]:
            deadline = time.monotonic() + int(runtime.get("timeout_seconds", 120))
            last_error = "not attempted"
            while time.monotonic() < deadline:
                status = 0
                body = ""
                try:
                    with urllib.request.urlopen(probe["url"], timeout=3) as response:
                        status = response.status
                        body = response.read().decode("utf-8", errors="replace")
                except urllib.error.HTTPError as exc:
                    status = exc.code
                    body = exc.read().decode("utf-8", errors="replace")
                except (urllib.error.URLError, TimeoutError) as exc:
                    last_error = str(exc)
                    time.sleep(2)
                    continue
                expected_status = int(probe.get("status", 200))
                expected_text = probe.get("contains", "")
                if status == expected_status and expected_text in body:
                    print(f"runtime probe passed: {probe['url']} -> {status}")
                    break
                last_error = f"HTTP {status}: {body[:120]}"
                time.sleep(2)
            else:
                raise RuntimeError(f"runtime probe timed out: {probe['url']}: {last_error}")
    finally:
        subprocess.run(stop, cwd=cwd, check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("static", "build", "compatibility", "runtime"), default="static")
    parser.add_argument("--scenario", action="append", help="Run only the named scenario; repeatable")
    args = parser.parse_args()

    scenarios = load_scenarios()
    selected = set(args.scenario or [])
    if selected:
        unknown = selected - {scenario["name"] for scenario in scenarios}
        if unknown:
            print(f"unknown scenarios: {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        scenarios = [scenario for scenario in scenarios if scenario["name"] in selected]

    errors = [error for scenario in scenarios for error in validate_scenario(scenario)]
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Static golden validation passed for {len(scenarios)} scenarios.")

    if args.mode == "static":
        return 0
    for scenario in scenarios:
        cwd = E2E_ROOT / scenario["after"]
        for command in scenario.get("build", []):
            run_command(command, cwd)
        if args.mode in {"compatibility", "runtime"}:
            for command in scenario.get("compatibility", []):
                run_command(command, cwd)
        if args.mode == "runtime" and scenario.get("runtime"):
            run_runtime(scenario["runtime"], cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
