"""Deterministic archive packaging."""

from __future__ import annotations

import gzip
import io
import json
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .hashing import sha256_bytes, sha256_file

_IGNORED_BUNDLE_NAMES = {"bundle.zip", "bundle.tar.gz", "MANIFEST.json"}


def create_bundle(directory: Path, *, fmt: str = "zip", source_date_epoch: int = 0) -> tuple[Path, dict[str, Any]]:
    if not directory.exists() or not directory.is_dir():
        raise ValidationError(f"package dir does not exist: {directory}")
    if source_date_epoch < 0:
        raise ValidationError("source_date_epoch must be >= 0")

    files = _sorted_payload_files(directory)
    manifest = {
        "version": 1,
        "files": [
            {
                "path": rel,
                "size": abs_path.stat().st_size,
                "sha256": sha256_file(abs_path),
            }
            for rel, abs_path in files
        ],
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")

    if fmt == "zip":
        bundle_path = directory / "bundle.zip"
        _write_zip(bundle_path, files, manifest_bytes, source_date_epoch)
    elif fmt == "tar.gz":
        bundle_path = directory / "bundle.tar.gz"
        _write_tar_gz(bundle_path, files, manifest_bytes, source_date_epoch)
    else:
        raise ValidationError("--format must be zip or tar.gz")

    return bundle_path, manifest


def checksum_for_bundle(path: Path) -> str:
    return sha256_file(path)


def checksum_for_manifest(manifest: dict[str, Any]) -> str:
    raw = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return sha256_bytes(raw)


def _sorted_payload_files(directory: Path) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        if path.name in _IGNORED_BUNDLE_NAMES:
            continue
        rel = path.relative_to(directory).as_posix()
        out.append((rel, path))
    out.sort(key=lambda x: x[0])
    return out


def _write_zip(bundle_path: Path, files: list[tuple[str, Path]], manifest_bytes: bytes, source_date_epoch: int) -> None:
    dt = _zip_datetime(source_date_epoch)
    with zipfile.ZipFile(bundle_path, mode="w", compression=zipfile.ZIP_STORED) as zf:
        for rel, abs_path in files:
            info = zipfile.ZipInfo(rel)
            info.date_time = dt
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, abs_path.read_bytes())

        manifest_info = zipfile.ZipInfo("MANIFEST.json")
        manifest_info.date_time = dt
        manifest_info.compress_type = zipfile.ZIP_STORED
        manifest_info.external_attr = 0o100644 << 16
        zf.writestr(manifest_info, manifest_bytes)


def _write_tar_gz(bundle_path: Path, files: list[tuple[str, Path]], manifest_bytes: bytes, source_date_epoch: int) -> None:
    with bundle_path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=source_date_epoch) as gz:
            with tarfile.open(fileobj=gz, mode="w") as tf:
                for rel, abs_path in files:
                    payload = abs_path.read_bytes()
                    info = _tar_info(rel, len(payload), source_date_epoch)
                    tf.addfile(info, io.BytesIO(payload))

                manifest_info = _tar_info("MANIFEST.json", len(manifest_bytes), source_date_epoch)
                tf.addfile(manifest_info, io.BytesIO(manifest_bytes))


def _tar_info(name: str, size: int, source_date_epoch: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = size
    info.mode = 0o644
    info.mtime = source_date_epoch
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    return info


def _zip_datetime(source_date_epoch: int) -> tuple[int, int, int, int, int, int]:
    floor = 315532800
    dt = datetime.fromtimestamp(max(source_date_epoch, floor), tz=timezone.utc)
    return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
