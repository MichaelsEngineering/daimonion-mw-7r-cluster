"""Manual stdlib-only config validator and memo path checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ValidationError

MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown"}


def validate_memo_path(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise ValidationError(f"memo does not exist: {path}")
    if path.suffix.lower() not in MARKDOWN_SUFFIXES:
        allowed = ", ".join(sorted(MARKDOWN_SUFFIXES))
        raise ValidationError(f"memo must be markdown ({allowed}): {path}")


def load_cluster_config(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise ValidationError(f"config does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"config is not valid JSON: {exc}") from exc
    return validate_cluster_config(payload)


def validate_cluster_config(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError("config must be an object")

    it_cap_w = _require_number(payload, "it_cap_w", positive=True)

    node = _require_object(payload, "node")
    gpu_count = _require_int(node, "gpu_count", minimum=1)
    gpu_power_w = _require_number(node, "gpu_power_w", positive=True)
    cpu_power_w = _require_number(node, "cpu_power_w", positive=True)
    baseboard_power_w = _require_number(node, "baseboard_power_w", positive=True)
    nic_power_w = _require_number(node, "nic_power_w", positive=True)
    storage_power_w = _require_number(node, "storage_power_w", positive=True)
    other_power_w = _require_number(node, "other_power_w", minimum=0)

    fabric = _require_object(payload, "fabric")
    host_ports_per_node = _require_int(fabric, "host_ports_per_node", minimum=1)
    host_link_gbps = _require_number(fabric, "host_link_gbps", positive=True)
    uplink_gbps = _require_number(fabric, "uplink_gbps", positive=True)
    optics_power_w_per_uplink = _require_number(fabric, "optics_power_w_per_uplink", minimum=0)

    leaf = _require_object(fabric, "leaf")
    leaf_ports = _require_int(leaf, "ports", minimum=1)
    leaf_host_ports = _require_int(leaf, "host_ports", minimum=1)
    leaf_uplink_ports = _require_int(leaf, "uplink_ports", minimum=1)
    leaf_power_w = _require_number(leaf, "power_w", positive=True)

    spine = _require_object(fabric, "spine")
    spine_ports = _require_int(spine, "ports", minimum=1)
    spine_power_w = _require_number(spine, "power_w", positive=True)

    if leaf_host_ports + leaf_uplink_ports > leaf_ports:
        raise ValidationError("leaf_host_ports + leaf_uplink_ports must be <= leaf.ports")
    if leaf_host_ports < host_ports_per_node:
        raise ValidationError("leaf.host_ports must be >= host_ports_per_node")
    if leaf_host_ports % host_ports_per_node != 0:
        raise ValidationError("leaf.host_ports must be divisible by host_ports_per_node")

    return {
        "it_cap_w": it_cap_w,
        "node": {
            "gpu_count": gpu_count,
            "gpu_power_w": gpu_power_w,
            "cpu_power_w": cpu_power_w,
            "baseboard_power_w": baseboard_power_w,
            "nic_power_w": nic_power_w,
            "storage_power_w": storage_power_w,
            "other_power_w": other_power_w,
        },
        "fabric": {
            "host_ports_per_node": host_ports_per_node,
            "host_link_gbps": host_link_gbps,
            "uplink_gbps": uplink_gbps,
            "optics_power_w_per_uplink": optics_power_w_per_uplink,
            "leaf": {
                "ports": leaf_ports,
                "host_ports": leaf_host_ports,
                "uplink_ports": leaf_uplink_ports,
                "power_w": leaf_power_w,
            },
            "spine": {
                "ports": spine_ports,
                "power_w": spine_power_w,
            },
        },
    }


def _require_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    if key not in payload:
        raise ValidationError(f"missing required key: {key}")
    value = payload[key]
    if not isinstance(value, dict):
        raise ValidationError(f"{key} must be an object")
    return value


def _require_number(
    payload: dict[str, Any],
    key: str,
    *,
    positive: bool = False,
    minimum: float | None = None,
) -> float:
    if key not in payload:
        raise ValidationError(f"missing required key: {key}")
    value = payload[key]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(f"{key} must be numeric")
    number = float(value)
    if positive and number <= 0:
        raise ValidationError(f"{key} must be > 0")
    if minimum is not None and number < minimum:
        raise ValidationError(f"{key} must be >= {minimum}")
    return number


def _require_int(payload: dict[str, Any], key: str, *, minimum: int) -> int:
    if key not in payload:
        raise ValidationError(f"missing required key: {key}")
    value = payload[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{key} must be an integer")
    if value < minimum:
        raise ValidationError(f"{key} must be >= {minimum}")
    return value
