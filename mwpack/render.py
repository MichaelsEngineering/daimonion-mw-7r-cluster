"""Best-effort rendering support."""

from __future__ import annotations

import html
import shutil
import subprocess
from pathlib import Path
from typing import Any


def render_memo(memo_path: Path, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "memo.html"
    pdf_path = out_dir / "memo.pdf"

    pandoc = shutil.which("pandoc")
    if pandoc:
        subprocess.run([pandoc, str(memo_path), "-o", str(html_path)], check=True)

        pdf_built = False
        pdf_error = ""
        try:
            subprocess.run([pandoc, str(memo_path), "-o", str(pdf_path)], check=True)
            pdf_built = True
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            pdf_error = str(exc)

        return {
            "renderer": "pandoc",
            "html": str(html_path),
            "pdf": str(pdf_path) if pdf_built else None,
            "pdf_error": pdf_error,
        }

    wrapper = (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head><meta charset=\"utf-8\"><title>memo fallback</title></head>\n"
        "<body><pre>"
        + html.escape(memo_path.read_text(encoding="utf-8"))
        + "</pre></body>\n"
        "</html>\n"
    )
    html_path.write_text(wrapper, encoding="utf-8")

    return {
        "renderer": "fallback-pre",
        "html": str(html_path),
        "pdf": None,
        "pdf_error": "pandoc not found",
    }
