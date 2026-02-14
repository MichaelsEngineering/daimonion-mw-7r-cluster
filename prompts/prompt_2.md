# Persona

You are my daimonion.

# Task

build the artifact

# Context

### ChatGPT 5.2 output

Short answer
Below is a repo-ready memo plus a dependency-free Python sizing tool (JSON-in, text/JSON-out) for “max GPUs under a fixed MW cap” with a simple fabric model (leaf-spine, oversubscription, multi-plane).

Plan or key points

1. Make all hardware numbers parameters, not claims. Defaults are placeholders.
2. Compute GPU-capacity bound by: IT power, network port math, switching power, optics.
3. Provide two modes: quick summary and JSON output for plots later.
4. Keep the memo readable and defensible: constraints, method, trade studies, final recommended config template.

Implementation or commands

`docs/5mw_cluster_memo.md`

```md
# Designing a 5 MW AI Cluster in Ashburn: Power-First Architecture

## 0. Executive summary

Given a fixed **IT power envelope** (example: **5.0 MW**), the cluster design is a constrained optimization: maximize **effective training throughput per MW** and **usable GPUs per MW**, subject to CPU/NIC/switch/optics power, port-radix limits, and acceptable oversubscription.

This memo provides:

1. A repeatable sizing method (SKU-level power model + fabric port math).
2. A network topology trade study (2-tier vs multi-plane, nonblocking vs oversubscription).
3. A recommended configuration template that can be instantiated for any GPU SKU and fabric.

All numeric assumptions are parameterized. The included tool computes feasible maxima from a JSON config.

---

## 1. Constraints and invariants

### 1.1 Hard constraints (inputs)

- **IT power envelope**: `P_it` (example: 5.0 MW). This is the critical power budget for compute + network + storage inside the data hall.
- **Redundancy regime**: N, N+1, or 2N upstream is out of scope here. If you have facility cap rather than IT cap, introduce PUE and redundancy losses explicitly.
- **Rack power limit**: `P_rack_max` (common ranges 30–120 kW depending on cooling and distro).
- **Cooling assumption**: air vs liquid. Affects allowable `P_rack_max` and occasionally per-node auxiliary power.

### 1.2 Design invariants (must hold)

- Every GPU must have a bounded path to the fabric with a defined oversubscription target.
- Per-node network must match the chosen training paradigm (data parallel, tensor/pipeline parallel, all-reduce sensitivity).
- Power model must include:
  - Compute (GPUs, CPUs, DRAM, local NVMe)
  - Node auxiliaries (fans, VRMs as a lumped “aux”)
  - Network endpoints (NICs)
  - Switching fabric + optics
  - Storage and management overhead (if present)

### 1.3 Output metrics (what “best” means)

- **Usable GPUs per MW**: `G / P_it`
- **Effective throughput per MW**: proxy via “network nonblockingness” and oversubscription for the target workload
- **TCO per effective GPU**: not computed here, but the tool outputs counts suitable for a cost model

---

## 2. SKU-level power model

We model cluster power as:

`P_total = P_compute_nodes + P_fabric + P_storage + P_misc`

### 2.1 Compute node model

A node type is defined by:

- `gpus_per_node`
- `gpu_w`
- `cpu_w`
- `dram_w`
- `nvme_w`
- `nics_per_node`
- `nic_w`
- `node_aux_w`

Then:
`P_node = gpus_per_node*gpu_w + cpu_w + dram_w + nvme_w + nics_per_node*nic_w + node_aux_w`

Cluster:
`P_compute_nodes = N_nodes * P_node`

### 2.2 Fabric model (leaf-spine, with oversubscription)

A fabric is defined by:

- `leaf`: `{ ports, host_ports, uplink_ports, switch_w }`
- `spine`: `{ ports, switch_w }`
- `optic_w_per_link` (optional lump per link end or per cable, define consistently)

Given:

- total host ports required: `H = N_nodes * nics_per_node * ports_per_nic_to_fabric`
- number of leaves: `L = ceil(H / leaf.host_ports)`
- uplinks per leaf: `U = leaf.uplink_ports` (or derived)
- total uplinks: `L * U`
- spines required: `S = ceil((L * U) / spine.ports)`

Then:
`P_switching = L*leaf.switch_w + S*spine.switch_w`

Optics:

- If each uplink consumes optics on both ends, model as:
  `P_optics = (L*U)*2*optic_w_per_link`
- If you have a per-cable number, adjust accordingly.

`P_fabric = P_switching + P_optics`

### 2.3 Oversubscription

Define oversubscription as:
`os = (total_host_bw) / (total_uplink_bw)`

If you keep uplink counts fixed, os emerges from the topology. If you target an os, solve for uplink ports per leaf (bounded by leaf port radix).

---

## 3. Topology trade study

### 3.1 Two-tier leaf-spine (baseline)

Pros:

- Predictable scaling, tractable cable plant, standard operations
- Works for RoCE and IB variants
  Cons:
- With fixed radix, nonblocking becomes expensive in spine count and optics
- For extremely latency-sensitive all-reduce, you may need multi-plane to reduce contention

Best when:

- You accept modest oversubscription for mixed training/inference
- You can afford enough uplinks to keep os near target

### 3.2 Three-tier (leaf-spine-super-spine)

Pros:

- Extends scale with smaller spines
  Cons:
- Adds latency and operational complexity
- Often inferior per-MW once optics are counted

Best when:

- Scale exceeds what 2-tier can address with available radix, and you must keep a single fabric

### 3.3 Multi-plane (two fabrics)

Pros:

- Reduces hot-spot contention and improves effective bisection
- Can tune per-plane oversubscription, isolate training vs inference
  Cons:
- Duplicates some switching/optics power
- More operational complexity

Best when:

- Training is dominant and you need stable all-reduce performance under high utilization

---

## 4. Recommended configuration template (instantiate with your SKU)

### 4.1 Step-by-step sizing procedure

1. Choose `P_it`, `P_rack_max`.
2. Choose node type and per-component power parameters.
3. Choose fabric (RoCE/IB) and switch/optic power parameters.
4. Run the sizing tool to compute feasible maxima for:
   - GPU count
   - node count
   - leaf/spine counts
   - rack count estimate (optional)
5. Check that:
   - rack power is feasible
   - oversubscription is acceptable
   - link counts/cable plant are within operational constraints

### 4.2 Output to record (for hiring loops)

- GPUs per MW for each fabric option
- Leaf/spine counts and optics power fraction
- Sensitivity: if GPU power increases by +X%, how many GPUs you lose at fixed MW
- Sensitivity: if optics power is higher/lower, how topology choice shifts

---

## 5. Example decision rule (no hard-coded vendor claims)

Given the same IT cap:

- If your workload is predominantly training with frequent all-reduce, prioritize:
  - lower oversubscription, multi-plane if needed
  - higher fabric power share is acceptable if it increases effective throughput per MW
- If your workload is mixed or inference-heavy:
  - accept higher oversubscription
  - bias toward simpler leaf-spine and lower optics footprint

---

## 6. Appendix: How to run the sizing tool

1. Create a config JSON (see `tools/example_5mw_config.json`).
2. Run:
   - `python tools/cluster_model.py --config tools/example_5mw_config.json`
3. Optional JSON output:
   - `python tools/cluster_model.py --config tools/example_5mw_config.json --json`

The tool prints:

- Total feasible nodes and GPUs under `P_it`
- Fabric leaf/spine counts and power
- GPUs per MW, and power breakdown
```

`tools/cluster_model.py`

```python
#!/usr/bin/env python3
"""
Power-first GPU cluster sizing tool (dependency-free).

Goal:
- Maximize GPU count under a fixed IT power envelope.
- Include compute nodes + fabric switching + optics.
- Simple leaf-spine model with parameterized radix and uplinks.

Inputs: JSON config
Outputs: human-readable summary or JSON.

This is deliberately conservative: it treats all listed components as part of the IT cap.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from typing import Any, Dict, Optional


def ceildiv(a: int, b: int) -> int:
    return (a + b - 1) // b


@dataclass(frozen=True)
class NodeType:
    name: str
    gpus_per_node: int
    gpu_w: float
    cpu_w: float
    dram_w: float
    nvme_w: float
    nics_per_node: int
    nic_w: float
    node_aux_w: float
    ports_per_nic_to_fabric: int = 1  # e.g., 1x400G; set >1 if bonding/dual links per NIC

    def power_w(self) -> float:
        return (
            self.gpus_per_node * self.gpu_w
            + self.cpu_w
            + self.dram_w
            + self.nvme_w
            + self.nics_per_node * self.nic_w
            + self.node_aux_w
        )

    def host_ports_required(self) -> int:
        return self.nics_per_node * self.ports_per_nic_to_fabric


@dataclass(frozen=True)
class Switch:
    name: str
    ports: int
    switch_w: float


@dataclass(frozen=True)
class Fabric:
    name: str
    leaf: Switch
    spine: Switch
    leaf_host_ports: int
    leaf_uplink_ports: int
    optic_w_per_link_end: float = 0.0  # per link end, multiplied by 2 per cable

    def validate(self) -> None:
        if self.leaf_host_ports + self.leaf_uplink_ports > self.leaf.ports:
            raise ValueError(
                f"Invalid fabric {self.name}: leaf_host_ports({self.leaf_host_ports})"
                f" + leaf_uplink_ports({self.leaf_uplink_ports}) > leaf.ports({self.leaf.ports})"
            )
        if self.leaf_host_ports <= 0 or self.leaf_uplink_ports <= 0:
            raise ValueError(f"Invalid fabric {self.name}: host/uplink ports must be > 0")
        if self.spine.ports <= 0:
            raise ValueError(f"Invalid fabric {self.name}: spine ports must be > 0")


@dataclass(frozen=True)
class Result:
    node_type: str
    fabric: str
    it_cap_w: float
    nodes: int
    gpus: int
    leaves: int
    spines: int
    host_ports: int
    uplinks_total: int
    p_node_total_w: float
    p_switching_w: float
    p_optics_w: float
    p_total_w: float

    def gpus_per_mw(self) -> float:
        return self.gpus / (self.it_cap_w / 1e6)


def parse_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_node(cfg: Dict[str, Any]) -> NodeType:
    n = cfg["node"]
    return NodeType(
        name=n["name"],
        gpus_per_node=int(n["gpus_per_node"]),
        gpu_w=float(n["gpu_w"]),
        cpu_w=float(n.get("cpu_w", 0.0)),
        dram_w=float(n.get("dram_w", 0.0)),
        nvme_w=float(n.get("nvme_w", 0.0)),
        nics_per_node=int(n.get("nics_per_node", 1)),
        nic_w=float(n.get("nic_w", 0.0)),
        node_aux_w=float(n.get("node_aux_w", 0.0)),
        ports_per_nic_to_fabric=int(n.get("ports_per_nic_to_fabric", 1)),
    )


def build_fabric(cfg: Dict[str, Any]) -> Fabric:
    f = cfg["fabric"]
    leaf = f["leaf"]
    spine = f["spine"]
    fabric = Fabric(
        name=f["name"],
        leaf=Switch(name=leaf["name"], ports=int(leaf["ports"]), switch_w=float(leaf["switch_w"])),
        spine=Switch(name=spine["name"], ports=int(spine["ports"]), switch_w=float(spine["switch_w"])),
        leaf_host_ports=int(f["leaf_host_ports"]),
        leaf_uplink_ports=int(f["leaf_uplink_ports"]),
        optic_w_per_link_end=float(f.get("optic_w_per_link_end", 0.0)),
    )
    fabric.validate()
    return fabric


def fabric_power_for_nodes(nodes: int, node: NodeType, fabric: Fabric) -> Dict[str, Any]:
    host_ports = nodes * node.host_ports_required()
    leaves = ceildiv(host_ports, fabric.leaf_host_ports)
    uplinks_total = leaves * fabric.leaf_uplink_ports
    spines = ceildiv(uplinks_total, fabric.spine.ports)

    p_switching = leaves * fabric.leaf.switch_w + spines * fabric.spine.switch_w
    # Each uplink consumes optics on both ends (leaf + spine) if optic_w_per_link_end is per end.
    p_optics = uplinks_total * 2.0 * fabric.optic_w_per_link_end

    return {
        "host_ports": host_ports,
        "leaves": leaves,
        "uplinks_total": uplinks_total,
        "spines": spines,
        "p_switching_w": p_switching,
        "p_optics_w": p_optics,
        "p_fabric_w": p_switching + p_optics,
    }


def solve_max_nodes(it_cap_w: float, node: NodeType, fabric: Fabric, min_nodes: int = 1) -> Result:
    # Upper bound: ignore fabric power first.
    p_node = node.power_w()
    if p_node <= 0:
        raise ValueError("Node power must be > 0")

    hi = int(it_cap_w // p_node)
    if hi < min_nodes:
        # Still compute the smallest case to show infeasibility.
        nodes = min_nodes
        fp = fabric_power_for_nodes(nodes, node, fabric)
        p_total = nodes * p_node + fp["p_fabric_w"]
        return Result(
            node_type=node.name,
            fabric=fabric.name,
            it_cap_w=it_cap_w,
            nodes=nodes,
            gpus=nodes * node.gpus_per_node,
            leaves=fp["leaves"],
            spines=fp["spines"],
            host_ports=fp["host_ports"],
            uplinks_total=fp["uplinks_total"],
            p_node_total_w=nodes * p_node,
            p_switching_w=fp["p_switching_w"],
            p_optics_w=fp["p_optics_w"],
            p_total_w=p_total,
        )

    # Binary search for max nodes with fabric included.
    lo = 0
    best: Optional[Result] = None
    while lo <= hi:
        mid = (lo + hi) // 2
        fp = fabric_power_for_nodes(mid, node, fabric)
        p_total = mid * p_node + fp["p_fabric_w"]
        if p_total <= it_cap_w:
            best = Result(
                node_type=node.name,
                fabric=fabric.name,
                it_cap_w=it_cap_w,
                nodes=mid,
                gpus=mid * node.gpus_per_node,
                leaves=fp["leaves"],
                spines=fp["spines"],
                host_ports=fp["host_ports"],
                uplinks_total=fp["uplinks_total"],
                p_node_total_w=mid * p_node,
                p_switching_w=fp["p_switching_w"],
                p_optics_w=fp["p_optics_w"],
                p_total_w=p_total,
            )
            lo = mid + 1
        else:
            hi = mid - 1

    if best is None:
        raise RuntimeError("No feasible solution found, check inputs.")
    return best


def format_w(w: float) -> str:
    if w >= 1e6:
        return f"{w/1e6:.3f} MW"
    if w >= 1e3:
        return f"{w/1e3:.1f} kW"
    return f"{w:.1f} W"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="Path to JSON config")
    ap.add_argument("--json", action="store_true", help="Emit JSON output")
    args = ap.parse_args()

    cfg = parse_config(args.config)
    it_cap_w = float(cfg["it_cap_mw"]) * 1e6

    node = build_node(cfg)
    fabric = build_fabric(cfg)

    res = solve_max_nodes(it_cap_w, node, fabric, min_nodes=int(cfg.get("min_nodes", 1)))

    if args.json:
        print(json.dumps(res.__dict__ | {"gpus_per_mw": res.gpus_per_mw()}, indent=2, sort_keys=True))
        return

    # Human output
    print(f"IT cap: {format_w(res.it_cap_w)}")
    print(f"Node type: {res.node_type}")
    print(f"Fabric: {res.fabric}")
    print("")
    print(f"Feasible nodes: {res.nodes}")
    print(f"Feasible GPUs:  {res.gpus}")
    print(f"GPUs per MW:    {res.gpus_per_mw():.2f}")
    print("")
    print("Fabric sizing:")
    print(f"  Host ports:   {res.host_ports}")
    print(f"  Leaves:       {res.leaves}")
    print(f"  Uplinks total:{res.uplinks_total}")
    print(f"  Spines:       {res.spines}")
    print("")
    print("Power breakdown:")
    print(f"  Nodes:        {format_w(res.p_node_total_w)}")
    print(f"  Switching:    {format_w(res.p_switching_w)}")
    print(f"  Optics:       {format_w(res.p_optics_w)}")
    print(f"  Total:        {format_w(res.p_total_w)}")


if __name__ == "__main__":
    main()
```

`tools/example_5mw_config.json` (placeholders, adjust to your SKU and fabric)

```json
{
  "it_cap_mw": 5.0,
  "min_nodes": 1,
  "node": {
    "name": "GPU-8x",
    "gpus_per_node": 8,
    "gpu_w": 700,
    "cpu_w": 700,
    "dram_w": 400,
    "nvme_w": 200,
    "nics_per_node": 8,
    "nic_w": 75,
    "node_aux_w": 350,
    "ports_per_nic_to_fabric": 1
  },
  "fabric": {
    "name": "LeafSpine-2tier",
    "leaf": { "name": "LeafSwitch", "ports": 64, "switch_w": 1200 },
    "spine": { "name": "SpineSwitch", "ports": 64, "switch_w": 1400 },
    "leaf_host_ports": 32,
    "leaf_uplink_ports": 32,
    "optic_w_per_link_end": 6.0
  }
}
```

Verify

1. Run: `python tools/cluster_model.py --config tools/example_5mw_config.json`
2. Check the output total does not exceed 5.0 MW.
3. Change `leaf_host_ports`, `leaf_uplink_ports`, and `optic_w_per_link_end` to see the fabric power fraction and GPU count sensitivity.
4. Swap node parameters (GPU power, NIC count) to match your target SKU and training topology.

# Verify

2026 github best practice for this artifact maker and Koopman Operator Theory for Multi-Agent Orchestration

# Output

plan, think new plan, output that plan
