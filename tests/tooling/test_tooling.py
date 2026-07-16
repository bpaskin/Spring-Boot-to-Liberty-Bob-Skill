#!/usr/bin/env python3
"""Deterministic tests for migration analysis, generation, and grading tools."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "migrate-spring-to-liberty" / "scripts"
FIXTURES = REPO_ROOT / "tests" / "fixtures"


def run_script(name: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *arguments],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class ToolingTests(unittest.TestCase):
    def test_analyzer_detects_spring_mvc_binding_expressions(self) -> None:
        inventory = json.loads(
            run_script("analyze_project.py", str(FIXTURES / "mvc-jpa-security")).stdout
        )
        frontend = next(item for item in inventory["capabilities"] if item["id"] == "frontend")
        markers = {item["marker"] for item in frontend["evidence"]}
        for marker in (
            "@ModelAttribute",
            "BindingResult",
            "@InitBinder",
            "th:field",
            "#fields",
            "webjars",
            "resolveLocale",
            "#{",
        ):
            self.assertIn(marker, markers)

    def test_characterization_includes_frontend_asset_layout_and_locale_cases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory_path = Path(directory) / "inventory.json"
            run_script(
                "analyze_project.py",
                str(FIXTURES / "mvc-jpa-security"),
                "--output",
                str(inventory_path),
            )
            result = json.loads(
                run_script(
                    "generate_characterization.py",
                    "--inventory",
                    str(inventory_path),
                ).stdout
            )
            cases = {item["id"] for item in result["cases"]}
            for case in (
                "frontend-asset-graph",
                "frontend-layout-parity",
                "frontend-locale-switch",
                "frontend-locale-session",
            ):
                self.assertIn(case, cases)

    def test_analyzer_detects_multi_module_complexity(self) -> None:
        result = run_script("analyze_project.py", str(FIXTURES / "multi-module-enterprise"))
        inventory = json.loads(result.stdout)
        self.assertTrue(inventory["build"]["multi_module"])
        self.assertEqual(
            inventory["recommended_migration"]["route"],
            "rehost-first-then-staged-slices",
        )
        capabilities = {item["id"] for item in inventory["capabilities"]}
        self.assertIn("messaging", capabilities)
        self.assertIn("security", capabilities)
        self.assertEqual(inventory["build"]["declared_module_names"], ["api", "worker"])

    def test_characterization_includes_complex_failure_cases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory_path = Path(directory) / "inventory.json"
            run_script(
                "analyze_project.py",
                str(FIXTURES / "reactive-cloud-custom"),
                "--output",
                str(inventory_path),
            )
            result = run_script(
                "generate_characterization.py",
                "--inventory",
                str(inventory_path),
            )
            cases = {item["id"] for item in json.loads(result.stdout)["cases"]}
            self.assertIn("reactive-backpressure", cases)
            self.assertIn("reactive-downstream-timeout", cases)
            self.assertIn("custom-extension-disabled", cases)
            self.assertIn("restart-recovery", cases)

            simple_inventory = Path(directory) / "simple-inventory.json"
            run_script(
                "analyze_project.py",
                str(FIXTURES / "rest-maven"),
                "--output",
                str(simple_inventory),
            )
            simple = json.loads(
                run_script(
                    "generate_characterization.py",
                    "--inventory",
                    str(simple_inventory),
                ).stdout
            )
            simple_cases = {item["id"] for item in simple["cases"]}
            self.assertNotIn("dependency-unavailable", simple_cases)

    def test_safe_codemod_is_dry_run_idempotent_and_selective(self) -> None:
        source = (
            "package demo;\n"
            "import javax.persistence.Entity;\n"
            "import javax.security.enterprise.SecurityContext;\n"
            "import javax.annotation.processing.Processor;\n"
            "import javax.transaction.xa.XAResource;\n"
            "import javax.sql.DataSource;\n"
            "import javax.cache.Cache;\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            java = root / "src" / "Demo.java"
            java.parent.mkdir(parents=True)
            java.write_text(source, encoding="utf-8")
            dry_run = json.loads(run_script("safe_codemods.py", str(root)).stdout)
            self.assertEqual(dry_run["changed_file_count"], 1)
            self.assertEqual(java.read_text(encoding="utf-8"), source)
            run_script("safe_codemods.py", str(root), "--apply", "--confirm-apply")
            migrated = java.read_text(encoding="utf-8")
            self.assertIn("jakarta.persistence.Entity", migrated)
            self.assertIn("jakarta.security.enterprise.SecurityContext", migrated)
            self.assertIn("javax.annotation.processing.Processor", migrated)
            self.assertIn("javax.transaction.xa.XAResource", migrated)
            self.assertIn("javax.sql.DataSource", migrated)
            self.assertIn("javax.cache.Cache", migrated)
            second = json.loads(run_script("safe_codemods.py", str(root)).stdout)
            self.assertEqual(second["changed_file_count"], 0)

    def test_liberty_rehost_scaffold_uses_detected_stream(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory_path = Path(directory) / "inventory.json"
            run_script(
                "analyze_project.py",
                str(FIXTURES / "rehost-spring-boot"),
                "--output",
                str(inventory_path),
            )
            result = run_script(
                "generate_liberty_config.py",
                "--inventory",
                str(inventory_path),
                "--scope",
                "rehost",
                "--artifact",
                "application.jar",
            )
            self.assertIn("<feature>springBoot-3.0</feature>", result.stdout)
            self.assertIn("<feature>servlet-6.0</feature>", result.stdout)
            self.assertIn('<springBootApplication id="application" location="application.jar">', result.stdout)
            ET.fromstring(result.stdout)

    def test_parity_grader_requires_matching_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "case.log"
            artifact.write_text("observed", encoding="utf-8")
            contract = {
                "schema_version": 1,
                "cases": [{"id": "case", "description": "case"}],
            }
            result = {
                "id": "case",
                "status": "PASS",
                "observed": "HTTP 200 with expected body",
                "signature": "http:200:sha256-demo",
                "artifact": "case.log",
            }
            baseline = {"schema_version": 1, "side": "baseline", "cases": [result]}
            target = {"schema_version": 1, "side": "target", "cases": [result]}
            for name, value in (
                ("contract.json", contract),
                ("baseline.json", baseline),
                ("target.json", target),
            ):
                (root / name).write_text(json.dumps(value), encoding="utf-8")
            completed = run_script(
                "verify_parity.py",
                "--contract",
                str(root / "contract.json"),
                "--baseline",
                str(root / "baseline.json"),
                "--target",
                str(root / "target.json"),
                "--evidence-root",
                str(root),
            )
            self.assertIn("Behavior parity evidence passed", completed.stdout)


if __name__ == "__main__":
    unittest.main()
