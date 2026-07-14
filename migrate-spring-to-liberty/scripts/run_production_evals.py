#!/usr/bin/env python3
"""Validate production integration fixtures and grade real case evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT / "tests" / "production"
MANIFEST = ROOT / "scenarios.json"


def load() -> list[dict]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("scenarios"), list):
        raise ValueError("tests/production/scenarios.json has an unsupported schema")
    return data["scenarios"]


def fixture_text(path: Path) -> str:
    parts: list[str] = []
    for item in sorted(path.rglob("*")):
        if not item.is_file() or item.name == "expected.json":
            continue
        try:
            parts.append(str(item.relative_to(path)))
            parts.append(item.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
    return "\n".join(parts)


def validate_manifest() -> list[str]:
    errors: list[str] = []
    required = {
        "postgres-xa-schema",
        "oidc-observability",
        "kafka-deployment",
    }
    names: set[str] = set()
    for scenario in load():
        name = scenario.get("name")
        if not isinstance(name, str) or not name or name in names:
            errors.append(f"invalid or duplicate production scenario: {name!r}")
            continue
        names.add(name)
        fixture = REPO_ROOT / scenario.get("fixture", "")
        if not fixture.is_dir():
            errors.append(f"{name}: fixture directory is missing")
            continue
        text = fixture_text(fixture)
        markers = scenario.get("required_markers")
        if not isinstance(markers, list) or not markers:
            errors.append(f"{name}: required_markers must be non-empty")
        else:
            for marker in markers:
                if not isinstance(marker, str) or marker not in text:
                    errors.append(f"{name}: fixture is missing marker {marker!r}")
        positive = scenario.get("positive_cases")
        failures = scenario.get("failure_cases")
        if not isinstance(positive, list) or not positive:
            errors.append(f"{name}: at least one positive case is required")
        if not isinstance(failures, list) or len(failures) < 3:
            errors.append(f"{name}: at least three real failure cases are required")
        for case in (positive or []) + (failures or []):
            if not isinstance(case, dict) or not all(case.get(field) for field in ("name", "trigger", "expected")):
                errors.append(f"{name}: each case needs name, trigger, and expected")
    if not required.issubset(names):
        errors.append(f"production scenarios are missing {sorted(required - names)}")
    return errors


def grade_evidence(scenarios: list[dict], evidence_root: Path) -> list[str]:
    errors: list[str] = []
    for scenario in scenarios:
        name = scenario["name"]
        evidence_file = evidence_root / f"{name}.json"
        if not evidence_file.is_file():
            errors.append(f"{name}: missing evidence file {evidence_file}")
            continue
        evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
        environment = evidence.get("environment")
        if evidence.get("scenario") != name or not isinstance(environment, dict):
            errors.append(f"{name}: evidence must name the scenario and describe a real environment")
        else:
            for field in ("liberty_version", "java_version", "infrastructure", "executed_at", "command"):
                if not environment.get(field):
                    errors.append(f"{name}: environment evidence is missing {field!r}")
        case_results = {
            case.get("name"): case
            for case in evidence.get("cases", [])
            if isinstance(case, dict)
        }
        required_cases = scenario["positive_cases"] + scenario["failure_cases"]
        for required in required_cases:
            result = case_results.get(required["name"])
            if result is None:
                errors.append(f"{name}: missing case evidence {required['name']!r}")
                continue
            if result.get("status") != "PASS":
                errors.append(
                    f"{name}: case {required['name']!r} is {result.get('status', 'UNKNOWN')}, not PASS"
                )
            if not result.get("observed"):
                errors.append(f"{name}: case {required['name']!r} lacks the observed result")
            artifact_value = result.get("artifact")
            if not artifact_value:
                errors.append(f"{name}: case {required['name']!r} lacks an artifact/log reference")
                continue
            artifact = Path(artifact_value)
            if artifact.is_absolute() or ".." in artifact.parts:
                errors.append(f"{name}: case {required['name']!r} artifact must be relative to the evidence root")
                continue
            artifact_path = evidence_root / artifact
            if not artifact_path.is_file() or artifact_path.stat().st_size == 0:
                errors.append(
                    f"{name}: case {required['name']!r} artifact does not exist or is empty: {artifact}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("static", "evidence"), default="static")
    parser.add_argument("--scenario", action="append")
    parser.add_argument("--evidence-root", type=Path)
    args = parser.parse_args()

    errors = validate_manifest()
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    scenarios = load()
    selected = set(args.scenario or [])
    if selected:
        known = {scenario["name"] for scenario in scenarios}
        unknown = selected - known
        if unknown:
            parser.error(f"unknown scenarios: {', '.join(sorted(unknown))}")
        scenarios = [scenario for scenario in scenarios if scenario["name"] in selected]
    if args.mode == "static":
        print(f"Production integration contracts passed for {len(scenarios)} scenarios.")
        return 0
    if args.evidence_root is None:
        parser.error("evidence mode requires --evidence-root")
    errors = grade_evidence(scenarios, args.evidence_root)
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Production integration evidence passed for {len(scenarios)} scenarios.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
