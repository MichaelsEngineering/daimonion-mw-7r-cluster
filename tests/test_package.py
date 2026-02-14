from __future__ import annotations

import json
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from mwpack import package
from mwpack.hashing import sha256_file


class PackageTests(unittest.TestCase):
    def test_bundle_contains_files_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "memo.md").write_text("hello\n", encoding="utf-8")
            (root / "cluster_report.json").write_text('{"ok":true}\n', encoding="utf-8")

            bundle, _ = package.create_bundle(root, fmt="zip", source_date_epoch=1_700_000_000)
            self.assertTrue(bundle.exists())

            with zipfile.ZipFile(bundle, "r") as zf:
                self.assertEqual(zf.namelist(), ["cluster_report.json", "memo.md", "MANIFEST.json"])
                manifest = json.loads(zf.read("MANIFEST.json").decode("utf-8"))
                lookup = {entry["path"]: entry for entry in manifest["files"]}
                self.assertEqual(lookup["memo.md"]["sha256"], sha256_file(root / "memo.md"))
                self.assertEqual(
                    lookup["cluster_report.json"]["sha256"],
                    sha256_file(root / "cluster_report.json"),
                )

    def test_zip_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "memo.md").write_text("memo\n", encoding="utf-8")
            (root / "cluster_report.json").write_text('{"nodes":0}\n', encoding="utf-8")

            b1, _ = package.create_bundle(root, fmt="zip", source_date_epoch=1_700_000_000)
            first = b1.read_bytes()
            b2, _ = package.create_bundle(root, fmt="zip", source_date_epoch=1_700_000_000)
            second = b2.read_bytes()
            self.assertEqual(first, second)

    def test_tar_gz_contains_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "memo.md").write_text("memo\n", encoding="utf-8")
            (root / "cluster_report.json").write_text('{"nodes":1}\n', encoding="utf-8")

            bundle, _ = package.create_bundle(root, fmt="tar.gz", source_date_epoch=1_700_000_000)
            with tarfile.open(bundle, "r:gz") as tf:
                self.assertEqual(tf.getnames(), ["cluster_report.json", "memo.md", "MANIFEST.json"])


if __name__ == "__main__":
    unittest.main()
