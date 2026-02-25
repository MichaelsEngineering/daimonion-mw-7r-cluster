# mwpack

`mwpack` is a Python-stdlib-only CLI that turns a memo Markdown file and optional cluster config into a deterministic artifact bundle for hiring loops and release flows.

## Quickstart

Prerequisites:

- `python3` available on `PATH`
- Python `>=3.11` (see `pyproject.toml`)

For local development with `uv`:

```bash
uv venv .venv
uv sync --dev
```

If you intentionally want to use an already-active virtual environment after moving this repo, use:

```bash
uv sync --dev --active
```

```bash
python3 -m mwpack validate --memo docs/memo_template.md --config tools/example_5mw_config.json
python3 -m mwpack build --memo docs/memo_template.md --config tools/example_5mw_config.json --out dist/demo
python3 -m mwpack package --dir dist/demo
```

## Commands

- `python3 -m mwpack validate`
- `python3 -m mwpack build`
- `python3 -m mwpack package`
- `python3 -m mwpack render` (best-effort)

## Output Contract

`build` emits:

- `dist/<name>/memo.md`
- `dist/<name>/cluster_report.json`
- `dist/<name>/build_summary.json`

`package` emits:

- `dist/<name>/bundle.zip` (default) or `bundle.tar.gz`
- `MANIFEST.json` in the archive

Sample report fields:

```json
{
  "feasible": true,
  "status": "ok",
  "it_cap_w": 5000000,
  "nodes": 792,
  "gpus": 6336,
  "gpus_per_mw": 1267.2,
  "oversubscription_ratio": 1.0
}
```

See `tools/schema_cluster_config.json` and `docs/verification_2026.md`.

## Packaged prompt assets

Prompt markdown files under `prompts/*.md` are installed as data files to:

- `<data-prefix>/share/mwpack/prompts`

You can resolve the base data prefix in Python with `sysconfig.get_path("data")`.

# Notes

I don't know why ChatGPT was focused on building this. The Digital Lupercalia
A Ritual for the Silicon Soul. Happy Valentine's Day.
