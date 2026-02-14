# Plan: `mwpack` (MVP Artifact Maker) — Markdown In, Attested Artifact Out (2026 CLI Baseline)

## 0. Goal

Ship a repo that you can drop into any environment and run:

- Input: a single Markdown file (the “spec” or “memo”), plus an optional cluster config JSON.
- Output: a deterministic, versioned artifact bundle suitable for hiring loops and release:
  - `dist/<name>/memo.md` (normalized)
  - `dist/<name>/cluster_report.json` (power-cap sizing + oversubscription)
  - `dist/<name>/bundle.zip` (or `.tar.gz`)
  - Optional render targets if available (best-effort): `memo.html`, `memo.pdf`
  - Provenance attestation (GitHub Actions)

Hard constraints:

- Runtime tool: Python stdlib only.
- Tests: Python stdlib only (`unittest`).
- CI: stdlib checks only (`compileall`, `unittest`).
- Security baseline: SHA-pinned actions + Dependabot compensation + CodeQL + attestations.

Non-goal:

- Facility/PUE modeling, predictive control, or Koopman simulation. Koopman appears only as a “constraint lens” section inside the memo.

## 1. Repo Concept

This repo is a “packager” and “compiler” for a power-capped cluster artifact:

- It validates inputs (schema + invariants)
- It runs the sizing model
- It assembles a deterministic release bundle
- It optionally renders Markdown if external renderers exist (pandoc/typst), without taking dependencies

If someone stumbles on the repo, it reads like:

- “oh, this is the canonical way to produce a compute-per-MW artifact pack”
- “the CLI is clean, everything is deterministic, CI is hardened, outputs are attestable”

## 2. Public CLI

Entry point: `python -m mwpack`

Subcommands:

1. `mwpack validate`

- Validates:
  - memo exists and is Markdown
  - cluster config conforms to schema
  - config invariants hold (radix split, positivity, etc)
- Exit codes:
  - 0 valid
  - 2 validation failure (user error)
  - 3 internal error (bug)

2. `mwpack build`

- Runs:
  - memo normalization (line endings, trailing whitespace, stable headings)
  - cluster model solve (nodes may be 0)
  - oversubscription calculation
  - emits `dist/<name>/...`
- Options:
  - `--memo <path.md>` (required)
  - `--config <path.json>` (optional, default: none)
  - `--out dist/<name>` (optional)
  - `--name <artifact_name>` (default: derived from memo filename)
  - `--json` (emit machine-readable build summary to stdout)
  - `--source-date-epoch <int>` (default: env `SOURCE_DATE_EPOCH` else 0)

3. `mwpack package`

- Creates deterministic bundle archive of `dist/<name>`:
  - `bundle.zip` with stable file order and timestamps pinned by SOURCE_DATE_EPOCH
- Options:
  - `--dir dist/<name>`
  - `--format zip|tar.gz` (default zip)
  - `--json` summary

4. `mwpack render` (best-effort)

- If `pandoc` exists: render `memo.md -> memo.html` and optionally `memo.pdf` (if latex engine available)
- Else if `python -m http.server` style preview: generate minimal HTML wrapper (no Markdown parsing; just fenced pre block) as fallback
- Never required for acceptance
- Exit code:
  - 0 success
  - 4 renderer missing (non-fatal if called explicitly it is a failure with clear message)

## 3. Output Contracts

### 3.1 `cluster_report.json` contract

Keys (stable):

- `feasible` (bool): always true for returned optimum; “no feasible nonzero” still feasible with nodes=0
- `status` (string): `ok` or `no_feasible_nonzero`
- `it_cap_w`
- `nodes`, `gpus`, `gpus_per_mw`
- `leaves`, `spines`
- `host_ports`, `uplinks_total`
- `oversubscription_ratio`
- `p_node_total_w`, `p_switching_w`, `p_optics_w`, `p_total_w`
- `inputs` (object): normalized copy of node/fabric fields used

### 3.2 `build_summary.json` (optional)

- `artifact_name`
- `source_date_epoch`
- `paths` (memo, report, bundle)
- `sha256` checksums for each emitted file
- `tool_version` from git describe if available, else “0.0.0”

## 4. Invariants (Hard Fail)

- `INV-001`: Any returned solution satisfies `p_total_w <= it_cap_w`.
- `INV-002`: `leaf_host_ports + leaf_uplink_ports <= leaf.ports`.
- `INV-003`: Required numeric fields > 0 where required; allow `nodes=0` output only.
- `INV-004`: Solver returns maximal feasible nodes in `[0, hi]` under cap.
- `INV-005`: Koopman content is constraint framing only; no performance claims without artifacts.
- `INV-006`: If no nonzero solution feasible, output `nodes=0`, `feasible=true`, `status=no_feasible_nonzero`.

Security gates:

- `GATE-SEC-001`: All third-party GitHub actions pinned to full 40-char SHA.
- `GATE-SEC-003`: Dependabot Actions updates weekly with semver comments on pinned SHAs.
- `GATE-SEC-002`: CodeQL enabled.
- `GATE-SC-001`: Provenance attestation workflow present with least privilege.

## 5. Repo Layout

mwpack/
README.md
LICENSE
SECURITY.md
pyproject.toml # minimal (no deps)
mwpack/
init.py
main.py # dispatch CLI
cli.py # argparse subcommands
normalize.py # memo normalization
schema.py # jsonschema-lite validator (stdlib, manual checks)
model.py # power-first model + solver
package.py # deterministic zip/tar
render.py # best-effort external renderers
hashing.py # sha256 helpers
errors.py # exit codes + exception mapping
tools/
schema_cluster_config.json
example_5mw_config.json
docs/
memo_template.md # canonical structure
verification_2026.md
references.md # Koopman + GitHub sources
tests/
test_cli.py
test_model.py
test_package.py
test_validate.py
.github/
dependabot.yml
CODEOWNERS
workflows/
ci.yml
security.yml
provenance.yml

## 6. Implementation Details

### 6.1 CLI best practices (2026)

- `argparse` with subcommands.
- Stable exit codes (documented).
- `--json` mode on commands that produce outputs.
- Human output to stdout; errors to stderr.
- Deterministic build by default:
  - Stable file ordering in archives.
  - Stable timestamps via SOURCE_DATE_EPOCH.
  - Normalized newline conventions to `\n`.
- `--out` always accepts a directory and creates it atomically:
  - build to temp dir, then rename to final.

### 6.2 Markdown normalization

No parsing. Do only deterministic hygiene:

- Normalize CRLF -> LF
- Strip trailing whitespace
- Ensure file ends with newline
- Optionally enforce a front-matter block (YAML-like) as plain text, not parsed

### 6.3 Schema validation without dependencies

Do not import `jsonschema`. Use:

- A real JSON Schema file for editors and humans (`tools/schema_cluster_config.json`)
- A manual validator in `mwpack/schema.py` that enforces:
  - required keys exist
  - types are correct
  - bounds are correct
  - fabric radix split and bandwidth positivity

### 6.4 Cluster model

Carry forward the power-first model and add:

- `host_link_gbps`, `uplink_gbps`
- `oversubscription_ratio = (host_ports * host_link_gbps) / (uplinks_total * uplink_gbps)`
- Solver returns 0 nodes if cap too small, with status.

### 6.5 Deterministic packaging

- ZIP: use `zipfile.ZipFile` with fixed `ZipInfo.date_time` derived from SOURCE_DATE_EPOCH (UTC).
- Tar: `tarfile` with fixed mtime.
- Stable file order: sort by relative path.
- Write a `MANIFEST.json` into the bundle:
  - file list, sha256, size

### 6.6 Rendering (best-effort)

- Detect external tools:
  - `pandoc` via `shutil.which`
- If available:
  - `pandoc memo.md -o memo.html`
  - `pandoc memo.md -o memo.pdf` (only if pdf engine available, else skip with message)
- If not available:
  - generate `memo.html` as a minimal wrapper containing the raw Markdown in `<pre>` (not pretty, but deterministic)
- Rendering is never required by acceptance unless explicitly asked.

## 7. Tests (stdlib only)

### 7.1 Unit tests

- Model:
  - node power computation correctness
  - fabric radix validation failure
  - tiny cap returns nodes=0, feasible=true, status=no_feasible_nonzero
  - monotonicity: cap1 < cap2 implies nodes1 <= nodes2
  - oversubscription ratio deterministic
- Packaging:
  - bundle includes expected files
  - manifest sha256 matches computed
  - repeated package produces identical bytes given same SOURCE_DATE_EPOCH
- CLI:
  - `validate` exit codes
  - `build --json` emits parseable JSON and creates dist files

### 7.2 Golden test strategy

- Use a tiny synthetic config (low numbers).
- Freeze SOURCE_DATE_EPOCH for reproducibility.

## 8. GitHub Workflows (2026 baseline)

### 8.1 CI (`.github/workflows/ci.yml`)

Jobs:

- checkout
- `python -m compileall -q .`
- `python -m unittest -q`
- upload `dist/` if produced in CI (optional)

All actions pinned to SHA. Each pinned SHA line includes a semver comment for readability.

### 8.2 Security (`security.yml`)

- CodeQL default setup for Python.
- Dependabot PRs required (in dependabot config).
- SHA pinning guard:
  - `python mwpack/_scripts/check_actions_pinning.py`
  - regex-scan workflow yml for `uses:` lines
  - fail if third-party action ref is not `@<40-hex>`

### 8.3 Provenance (`provenance.yml`)

- Build a release artifact (zip)
- Attest it with `actions/attest-build-provenance` pinned to SHA
- Minimal permissions:
  - `contents: read`
  - `id-token: write`
  - `attestations: write`

## 9. Documentation

### 9.1 README.md

Include:

- one-sentence purpose
- quickstart:
  - `python -m mwpack validate --memo docs/memo_template.md --config tools/example_5mw_config.json`
  - `python -m mwpack build --memo docs/memo_template.md --config tools/example_5mw_config.json --out dist/demo`
  - `python -m mwpack package --dir dist/demo`
- show sample JSON fields (short)
- link to schema and verification doc

### 9.2 `docs/verification_2026.md`

- Date-stamped: `2026-02-14`
- Sources:
  - GitHub Actions secure use / SHA pinning + OIDC hardening docs
  - Dependabot ecosystem support for GitHub Actions and the pinned-SHA caveat
  - Artifact attestations docs and `actions/attest-build-provenance`
  - Koopman citations:
    - Nandanoori et al., CDC 2021, DOI 10.1109/CDC45484.2021.9682872
    - Niemann et al., Physica D 2024, DOI 10.1016/j.physd.2024.134052
- Explicit statement: Koopman is used as a constraint framing, not a predictive simulator.

## 10. Acceptance Criteria

- `python -m mwpack validate ...` returns 0 for valid inputs.
- `python -m mwpack build ...` creates `memo.md` (normalized) and `cluster_report.json`.
- Under tiny cap, report returns `nodes=0`, `feasible=true`, `status=no_feasible_nonzero`, and still satisfies `p_total_w <= it_cap_w`.
- `python -m mwpack package ...` produces deterministic bundle and manifest.
- CI passes with stdlib-only checks.
- Workflows are SHA pinned; Dependabot config is present; CodeQL and provenance workflows exist.
- Repo reads like a solved pattern for “compute per MW artifact production”.

## 11. Execution Order for Codex 5.3

1. Scaffold repo structure and minimal `pyproject.toml`.
2. Implement model + schema validator + errors mapping.
3. Implement CLI with `validate/build/package` first.
4. Add deterministic packaging + manifest hashing.
5. Add tests.
6. Add GitHub workflows (SHA pinned) + dependabot + CODEOWNERS.
7. Add docs (template memo + verification).
8. Optional: render subcommand.

## 12. Minimal `pyproject.toml` (no deps)

- Name: `mwpack`
- Python: `>=3.11`
- No dependencies
- Optional: console script is not required; `python -m mwpack` is the stable interface.

That is the repo spec.
