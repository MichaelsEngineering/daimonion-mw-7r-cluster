"""Power-first cluster model and solver."""

from __future__ import annotations

import math
from typing import Any

from .errors import ValidationError


def compute_node_power_w(config: dict[str, Any]) -> float:
    node = config["node"]
    return (
        node["gpu_count"] * node["gpu_power_w"]
        + node["cpu_power_w"]
        + node["baseboard_power_w"]
        + node["nic_power_w"]
        + node["storage_power_w"]
        + node["other_power_w"]
    )


def evaluate_cluster(config: dict[str, Any], nodes: int) -> dict[str, Any]:
    if nodes < 0:
        raise ValidationError("nodes must be >= 0")

    it_cap_w = config["it_cap_w"]
    node = config["node"]
    fabric = config["fabric"]
    leaf = fabric["leaf"]
    spine = fabric["spine"]

    host_ports = nodes * fabric["host_ports_per_node"]
    if host_ports == 0:
        leaves = 0
        uplinks_total = 0
        spines = 0
    else:
        leaves = math.ceil(host_ports / leaf["host_ports"])
        uplinks_total = leaves * leaf["uplink_ports"]
        spines = math.ceil(uplinks_total / spine["ports"]) if uplinks_total else 0

    p_node_total_w = nodes * compute_node_power_w(config)
    p_switching_w = leaves * leaf["power_w"] + spines * spine["power_w"]
    p_optics_w = uplinks_total * fabric["optics_power_w_per_uplink"]
    p_total_w = p_node_total_w + p_switching_w + p_optics_w

    if uplinks_total == 0:
        oversubscription_ratio = 0.0
    else:
        oversubscription_ratio = (
            host_ports * fabric["host_link_gbps"]
        ) / (uplinks_total * fabric["uplink_gbps"])

    gpus = nodes * node["gpu_count"]
    gpus_per_mw = 0.0 if it_cap_w <= 0 else gpus / (it_cap_w / 1_000_000.0)

    return {
        "feasible": p_total_w <= it_cap_w,
        "status": "ok",
        "it_cap_w": it_cap_w,
        "nodes": nodes,
        "gpus": gpus,
        "gpus_per_mw": gpus_per_mw,
        "leaves": leaves,
        "spines": spines,
        "host_ports": host_ports,
        "uplinks_total": uplinks_total,
        "oversubscription_ratio": oversubscription_ratio,
        "p_node_total_w": p_node_total_w,
        "p_switching_w": p_switching_w,
        "p_optics_w": p_optics_w,
        "p_total_w": p_total_w,
        "inputs": {
            "node": node,
            "fabric": fabric,
        },
    }


def solve_max_nodes(config: dict[str, Any]) -> dict[str, Any]:
    cap = config["it_cap_w"]
    node_power = compute_node_power_w(config)
    if node_power <= 0:
        raise ValidationError("computed node power must be > 0")

    hi = int(cap // node_power)
    lo = 0
    best = 0

    while lo <= hi:
        mid = (lo + hi) // 2
        trial = evaluate_cluster(config, mid)
        if trial["p_total_w"] <= cap:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    report = evaluate_cluster(config, best)
    report["feasible"] = True
    report["status"] = "ok" if best > 0 else "no_feasible_nonzero"

    if report["p_total_w"] > cap:
        raise RuntimeError("INV-001 violated: p_total_w > it_cap_w")
    if report["inputs"]["fabric"]["leaf"]["host_ports"] + report["inputs"]["fabric"]["leaf"]["uplink_ports"] > report["inputs"]["fabric"]["leaf"]["ports"]:
        raise RuntimeError("INV-002 violated: leaf host+uplink exceeds radix")

    return report


def empty_cluster_report() -> dict[str, Any]:
    return {
        "feasible": True,
        "status": "no_feasible_nonzero",
        "it_cap_w": 0.0,
        "nodes": 0,
        "gpus": 0,
        "gpus_per_mw": 0.0,
        "leaves": 0,
        "spines": 0,
        "host_ports": 0,
        "uplinks_total": 0,
        "oversubscription_ratio": 0.0,
        "p_node_total_w": 0.0,
        "p_switching_w": 0.0,
        "p_optics_w": 0.0,
        "p_total_w": 0.0,
        "inputs": {},
    }
