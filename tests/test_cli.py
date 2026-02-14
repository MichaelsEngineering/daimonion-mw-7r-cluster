from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "mwpack", *args],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_validate_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            memo = tmpdir / "memo.md"
            memo.write_text("# memo\n", encoding="utf-8")

            valid = self.run_cli(
                [
                    "validate",
                    "--memo",
                    str(memo),
                    "--config",
                    str(ROOT / "tools" / "example_5mw_config.json"),
                ]
            )
            self.assertEqual(valid.returncode, 0)

            bad_cfg = tmpdir / "bad.json"
            bad_cfg.write_text('{"it_cap_w": 100}', encoding="utf-8")
            invalid = self.run_cli([
                "validate",
                "--memo",
                str(memo),
                "--config",
                str(bad_cfg),
            ])
            self.assertEqual(invalid.returncode, 2)

    def test_build_json_output_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            memo = tmpdir / "memo.md"
            memo.write_text("# memo\n", encoding="utf-8")
            out = tmpdir / "dist" / "demo"

            result = self.run_cli(
                [
                    "build",
                    "--memo",
                    str(memo),
                    "--config",
                    str(ROOT / "tools" / "example_5mw_config.json"),
                    "--out",
                    str(out),
                    "--json",
                    "--source-date-epoch",
                    "1700000000",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["artifact_name"], "memo")
            self.assertTrue((out / "memo.md").exists())
            self.assertTrue((out / "cluster_report.json").exists())
            self.assertTrue((out / "build_summary.json").exists())


if __name__ == "__main__":
    unittest.main()
