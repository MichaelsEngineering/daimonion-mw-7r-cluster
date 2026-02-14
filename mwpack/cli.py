"""CLI parser and subcommands."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from . import model, normalize, package, render, schema
from .errors import ExitCode, RendererMissingError, ValidationError
from .hashing import sha256_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mwpack")
    sub = parser.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate memo and optional config")
    v.add_argument("--memo", required=True, type=Path)
    v.add_argument("--config", type=Path)
    v.set_defaults(func=_cmd_validate)

    b = sub.add_parser("build", help="build deterministic artifact directory")
    b.add_argument("--memo", required=True, type=Path)
    b.add_argument("--config", type=Path)
    b.add_argument("--out", type=Path)
    b.add_argument("--name")
    b.add_argument("--json", action="store_true")
    b.add_argument("--source-date-epoch", type=int)
    b.set_defaults(func=_cmd_build)

    p = sub.add_parser("package", help="package deterministic archive")
    p.add_argument("--dir", required=True, type=Path)
    p.add_argument("--format", default="zip", choices=["zip", "tar.gz"])
    p.add_argument("--json", action="store_true")
    p.add_argument("--source-date-epoch", type=int)
    p.set_defaults(func=_cmd_package)

    r = sub.add_parser("render", help="best-effort rendering")
    r.add_argument("--memo", required=True, type=Path)
    r.add_argument("--out", type=Path)
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=_cmd_render)

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


def _cmd_validate(args: argparse.Namespace) -> int:
    schema.validate_memo_path(args.memo)
    if args.config:
        schema.load_cluster_config(args.config)
    return int(ExitCode.OK)


def _cmd_build(args: argparse.Namespace) -> int:
    source_date_epoch = _resolve_source_date_epoch(args.source_date_epoch)

    schema.validate_memo_path(args.memo)

    config: dict[str, Any] | None = None
    if args.config is not None:
        config = schema.load_cluster_config(args.config)

    name = _artifact_name(args.name, args.memo)
    out_dir = args.out if args.out is not None else Path("dist") / name
    out_dir = out_dir.resolve()
    out_dir.parent.mkdir(parents=True, exist_ok=True)

    temp_build_dir = Path(tempfile.mkdtemp(prefix=f".{name}.", dir=str(out_dir.parent)))
    moved = False
    try:
        memo_out = temp_build_dir / "memo.md"
        report_out = temp_build_dir / "cluster_report.json"

        normalize.normalize_markdown_file(args.memo, memo_out)

        report = model.solve_max_nodes(config) if config is not None else model.empty_cluster_report()
        report_out.write_text(_json(report), encoding="utf-8")

        summary = {
            "artifact_name": name,
            "source_date_epoch": source_date_epoch,
            "paths": {
                "memo": str(out_dir / "memo.md"),
                "report": str(out_dir / "cluster_report.json"),
                "summary": str(out_dir / "build_summary.json"),
                "bundle": str(out_dir / "bundle.zip"),
            },
            "sha256": {
                "memo": sha256_file(memo_out),
                "report": sha256_file(report_out),
            },
            "tool_version": _tool_version(),
        }
        summary_out = temp_build_dir / "build_summary.json"
        summary_out.write_text(_json(summary), encoding="utf-8")

        if out_dir.exists():
            cwd = Path.cwd().resolve()
            home = Path.home().resolve()
            if out_dir in {Path("/"), home, cwd} or cwd.is_relative_to(out_dir):
                raise ValidationError(f"unsafe output directory: {out_dir}")
            shutil.rmtree(out_dir)
        os.replace(temp_build_dir, out_dir)
        moved = True

        if args.json:
            print(_json(summary).strip())
        else:
            print(f"Built artifact directory: {out_dir}")

        return int(ExitCode.OK)
    finally:
        if not moved and temp_build_dir.exists():
            shutil.rmtree(temp_build_dir, ignore_errors=True)


def _cmd_package(args: argparse.Namespace) -> int:
    source_date_epoch = _resolve_source_date_epoch(args.source_date_epoch)
    bundle_path, manifest = package.create_bundle(
        args.dir,
        fmt=args.format,
        source_date_epoch=source_date_epoch,
    )

    summary = {
        "format": args.format,
        "bundle": str(bundle_path),
        "source_date_epoch": source_date_epoch,
        "sha256": package.checksum_for_bundle(bundle_path),
        "manifest_sha256": package.checksum_for_manifest(manifest),
        "files": len(manifest["files"]),
    }

    if args.json:
        print(_json(summary).strip())
    else:
        print(f"Packaged bundle: {bundle_path}")

    return int(ExitCode.OK)


def _cmd_render(args: argparse.Namespace) -> int:
    schema.validate_memo_path(args.memo)
    out_dir = args.out if args.out is not None else args.memo.parent
    result = render.render_memo(args.memo, out_dir)

    if args.json:
        print(_json(result).strip())
    else:
        print(f"Rendered HTML: {result['html']}")
        if result["pdf"]:
            print(f"Rendered PDF: {result['pdf']}")
        elif result["pdf_error"]:
            print(result["pdf_error"])

    if result["renderer"] == "fallback-pre":
        raise RendererMissingError("pandoc not found; fallback HTML created")

    return int(ExitCode.OK)


def _resolve_source_date_epoch(value: int | None) -> int:
    if value is not None:
        if value < 0:
            raise ValidationError("--source-date-epoch must be >= 0")
        return value

    env = os.getenv("SOURCE_DATE_EPOCH")
    if env is None:
        return 0
    try:
        parsed = int(env)
    except ValueError as exc:
        raise ValidationError("SOURCE_DATE_EPOCH must be an integer") from exc

    if parsed < 0:
        raise ValidationError("SOURCE_DATE_EPOCH must be >= 0")
    return parsed


def _artifact_name(cli_name: str | None, memo_path: Path) -> str:
    raw = cli_name if cli_name else memo_path.stem
    chars = [c.lower() if c.isalnum() else "-" for c in raw.strip()]
    normalized = "".join(chars).strip("-")
    return normalized or "artifact"


def _tool_version() -> str:
    try:
        proc = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "0.0.0"
    if proc.returncode != 0:
        return "0.0.0"
    value = proc.stdout.strip()
    return value if value else "0.0.0"


def _json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
