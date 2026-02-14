from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mwpack import schema
from mwpack.errors import ValidationError


class ValidateTests(unittest.TestCase):
    def test_markdown_memo_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memo = Path(tmp) / "memo.md"
            memo.write_text("# memo\n", encoding="utf-8")
            schema.validate_memo_path(memo)

    def test_non_markdown_memo_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            memo = Path(tmp) / "memo.txt"
            memo.write_text("memo\n", encoding="utf-8")
            with self.assertRaises(ValidationError):
                schema.validate_memo_path(memo)

    def test_invalid_bandwidth_rejected(self) -> None:
        payload = {
            "it_cap_w": 1000,
            "node": {
                "gpu_count": 1,
                "gpu_power_w": 100,
                "cpu_power_w": 10,
                "baseboard_power_w": 10,
                "nic_power_w": 10,
                "storage_power_w": 10,
                "other_power_w": 0,
            },
            "fabric": {
                "host_ports_per_node": 1,
                "host_link_gbps": 0,
                "uplink_gbps": 100,
                "optics_power_w_per_uplink": 1,
                "leaf": {
                    "ports": 4,
                    "host_ports": 2,
                    "uplink_ports": 2,
                    "power_w": 10,
                },
                "spine": {
                    "ports": 4,
                    "power_w": 10,
                },
            },
        }
        with self.assertRaises(ValidationError):
            schema.validate_cluster_config(payload)


if __name__ == "__main__":
    unittest.main()
