#!/usr/bin/env python3
"""Prepare, run, and grade black-box agent migration evaluations."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "migrate-spring-to-liberty"
EVAL_ROOT = REPO_ROOT / "tests" / "agent-evals"
MANIFEST = EVAL_ROOT / "scenarios.json"
IGNORED_PARTS = {".git", ".gradle", "build", "target", "__pycache__"}


def load_scenarios() -> list[dict]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("scenarios"), list):
        raise ValueError("tests/agent-evals/scenarios.json has an unsupported schema")
    return data["scenarios"]


def scenario_by_name(name: str) -> dict:
    for scenario in load_scenarios():
        if scenario.get("name") == name:
            return scenario
    raise ValueError(f"unknown agent evaluation scenario: {name}")


def scenario_source(scenario: dict) -> Path:
    source = (EVAL_ROOT / scenario.get("source", "")).resolve()
    try:
        source.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{scenario.get('name')}: source escapes the repository") from exc
    return source


def tree_text(root: Path) -> str:
    parts: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        try:
            parts.append(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
    return "\n".join(parts)


def validate_manifest() -> list[str]:
    errors: list[str] = []
    names: set[str] = set()
    for scenario in load_scenarios():
        name = scenario.get("name")
        if not isinstance(name, str) or not name or name in names:
            errors.append(f"invalid or duplicate agent evaluation name: {name!r}")
            continue
        names.add(name)
        try:
            source = scenario_source(scenario)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        prompt = EVAL_ROOT / scenario.get("prompt", "")
        if not source.is_dir():
            errors.append(f"{name}: source directory is missing")
        if not prompt.is_file():
            errors.append(f"{name}: prompt file is missing")
        else:
            try:
                prompt.read_text(encoding="utf-8").format(
                    workspace="/isolated/workspace",
                    skill_path="/isolated/skill",
                    contract=scenario.get("contract", ""),
                )
            except (KeyError, ValueError) as exc:
                errors.append(f"{name}: prompt template cannot be rendered: {exc}")
        if scenario.get("prompt") == "contract/prompt.md" and not scenario.get("contract"):
            errors.append(f"{name}: contract prompt requires a non-empty contract")
        for field in ("required_paths", "required_text", "forbidden_text"):
            value = scenario.get(field)
            if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
                errors.append(f"{name}: {field} must be a string array")
        for command in scenario.get("build", []):
            if not isinstance(command, list) or not command or not all(isinstance(arg, str) for arg in command):
                errors.append(f"{name}: build commands must be non-empty argument arrays")
    required = {
        "simple-rest-rewrite",
        "mvc-data-security-rewrite",
        "messaging-staged",
        "batch-staged",
        "data-xa-staged",
        "identity-observability-staged",
        "reactive-cloud-staged",
        "multi-module-staged",
        "boot3-rehost",
        "boot4-rehost",
    }
    if not required.issubset(names):
        errors.append(f"agent evaluations are missing {sorted(required - names)}")
    return errors


def prepare_workspace(scenario: dict, workspace: Path) -> None:
    source = scenario_source(scenario)
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError(f"workspace must be absent or empty: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, workspace, dirs_exist_ok=True)


def grade(scenario: dict, workspace: Path, execute_build: bool) -> list[str]:
    errors: list[str] = []
    if not workspace.is_dir():
        return [f"candidate workspace does not exist: {workspace}"]
    text = tree_text(workspace)
    for relative in scenario["required_paths"]:
        if not (workspace / relative).is_file():
            errors.append(f"missing required path: {relative}")
    for marker in scenario["required_text"]:
        if marker not in text:
            errors.append(f"missing required migration evidence: {marker!r}")
    for marker in scenario["forbidden_text"]:
        if marker in text:
            errors.append(f"forbidden migration residue found: {marker!r}")
    if scenario.get("forbid_unresolved_migration_todo") and "TODO: Migration required" in text:
        errors.append("candidate contains an unresolved migration TODO")
    if execute_build and not errors:
        for command in scenario.get("build", []):
            print(f"[{workspace.name}] $ {' '.join(command)}", flush=True)
            try:
                subprocess.run(command, cwd=workspace, check=True)
            except subprocess.CalledProcessError as exc:
                errors.append(f"build command failed with exit {exc.returncode}: {' '.join(command)}")
                break
    return errors


def resolve_agent_command(raw: str, workspace: Path, prompt_file: Path) -> list[str]:
    try:
        command = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"agent command is not valid JSON: {exc}") from exc
    if not isinstance(command, list) or not command or not all(isinstance(arg, str) for arg in command):
        raise ValueError("agent command must be a non-empty JSON string array")
    values = {
        "workspace": str(workspace),
        "prompt_file": str(prompt_file),
        "skill_path": str(SKILL_ROOT),
    }
    return [arg.format_map(values) for arg in command]


def run_agent(scenario: dict, command_json: str, keep_workspace: bool) -> int:
    temp = Path(tempfile.mkdtemp(prefix=f"liberty-agent-eval-{scenario['name']}-"))
    workspace = temp / "workspace"
    try:
        prepare_workspace(scenario, workspace)
        prompt_template = (EVAL_ROOT / scenario["prompt"]).read_text(encoding="utf-8")
        prompt_file = temp / "prompt.md"
        prompt_file.write_text(
            prompt_template.format(
                workspace=workspace,
                skill_path=SKILL_ROOT,
                contract=scenario.get("contract", ""),
            ),
            encoding="utf-8",
        )
        command = resolve_agent_command(command_json, workspace, prompt_file)
        print(f"running black-box agent command: {command[0]} ...", flush=True)
        subprocess.run(command, cwd=REPO_ROOT, check=True)
        errors = grade(scenario, workspace, execute_build=True)
        if errors:
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(f"Agent evaluation passed: {scenario['name']}")
        return 0
    finally:
        if keep_workspace:
            print(f"kept agent evaluation workspace: {workspace}")
        else:
            shutil.rmtree(temp, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("static", "prepare", "grade", "run"), default="static")
    parser.add_argument("--scenario", default="simple-rest-rewrite")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--execute-build", action="store_true")
    parser.add_argument("--agent-command-json", help="JSON argument array; supports {workspace}, {prompt_file}, and {skill_path}")
    parser.add_argument("--keep-workspace", action="store_true")
    args = parser.parse_args()

    errors = validate_manifest()
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if args.mode == "static":
        print(f"Agent evaluation manifest passed for {len(load_scenarios())} scenarios.")
        return 0

    scenario = scenario_by_name(args.scenario)
    if args.mode in {"prepare", "grade"} and args.workspace is None:
        parser.error("--workspace is required for prepare and grade modes")
    if args.mode == "prepare":
        prepare_workspace(scenario, args.workspace)
        print(f"Prepared agent evaluation workspace: {args.workspace}")
        return 0
    if args.mode == "grade":
        errors = grade(scenario, args.workspace, args.execute_build)
        if errors:
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print(f"Agent evaluation candidate passed: {scenario['name']}")
        return 0

    command_json = args.agent_command_json or os.environ.get("AGENT_EVAL_COMMAND_JSON")
    if not command_json:
        parser.error("run mode requires --agent-command-json or AGENT_EVAL_COMMAND_JSON")
    return run_agent(scenario, command_json, args.keep_workspace)


if __name__ == "__main__":
    raise SystemExit(main())
