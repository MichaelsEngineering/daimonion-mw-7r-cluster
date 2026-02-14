from __future__ import annotations

import copy
import unittest

from mwpack import model, schema
from mwpack.errors import ValidationError


BASE_CONFIG = {
    "it_cap_w": 5_000_000,
    "node": {
        "gpu_count": 8,
        "gpu_power_w": 700,
        "cpu_power_w": 350,
        "baseboard_power_w": 120,
        "nic_power_w": 80,
        "storage_power_w": 60,
        "other_power_w": 40,
    },
    "fabric": {
        "host_ports_per_node": 1,
        "host_link_gbps": 400,
        "uplink_gbps": 400,
        "optics_power_w_per_uplink": 8,
        "leaf": {
            "ports": 64,
            "host_ports": 32,
            "uplink_ports": 32,
            "power_w": 450,
        },
        "spine": {
            "ports": 64,
            "power_w": 500,
        },
    },
}


class ModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = schema.validate_cluster_config(copy.deepcopy(BASE_CONFIG))

    def test_node_power_computation(self) -> None:
        self.assertEqual(model.compute_node_power_w(self.config), 6250.0)

    def test_radix_validation_failure(self) -> None:
        bad = copy.deepcopy(BASE_CONFIG)
        bad["fabric"]["leaf"]["host_ports"] = 40
        bad["fabric"]["leaf"]["uplink_ports"] = 30
        with self.assertRaises(ValidationError):
            schema.validate_cluster_config(bad)

    def test_tiny_cap_returns_zero_nodes_and_feasible_true(self) -> None:
        tiny = copy.deepcopy(self.config)
        tiny["it_cap_w"] = 500.0
        report = model.solve_max_nodes(tiny)
        self.assertEqual(report["nodes"], 0)
        self.assertTrue(report["feasible"])
        self.assertEqual(report["status"], "no_feasible_nonzero")
        self.assertLessEqual(report["p_total_w"], report["it_cap_w"])

    def test_monotonicity(self) -> None:
        c1 = copy.deepcopy(self.config)
        c2 = copy.deepcopy(self.config)
        c1["it_cap_w"] = 2_000_000.0
        c2["it_cap_w"] = 4_000_000.0
        n1 = model.solve_max_nodes(c1)["nodes"]
        n2 = model.solve_max_nodes(c2)["nodes"]
        self.assertLessEqual(n1, n2)

    def test_oversubscription_deterministic(self) -> None:
        r1 = model.solve_max_nodes(self.config)
        r2 = model.solve_max_nodes(self.config)
        self.assertEqual(r1["oversubscription_ratio"], r2["oversubscription_ratio"])


if __name__ == "__main__":
    unittest.main()
