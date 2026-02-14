# Persona

You are an expert at maximum compute per megawatt

# Task

create a repo that assumes you have a .md file and converts that into the correct output artifact using cli best practices 2026

# Context

### plan

# Plan v2: MVP Artifact Maker (Power-Capped Cluster) with Consistent Solver Semantics and 2026 GitHub Security Baseline

## Summary

Deliver a repo-ready MVP artifact pack that is internally consistent and implementation-ready:

1. `docs/5mw_cluster_memo.md` with explicit assumptions and Koopman-as-constraint framing.
2. `tools/cluster_model.py` (stdlib-only) with deterministic max-node solve under IT cap.
3. Config + schema + tests, including explicit no-feasible-case behavior.
4. GitHub CI/security/provenance workflows aligned with 2026 practices (SHA pinning, Dependabot compensation, attestations).
5. Verification doc with explicit citations (GitHub + Koopman literature).

Selected defaults (locked):

- No-feasible behavior: return `nodes=0` (valid feasible optimum).
- Oversubscription: computed in tool using bandwidth fields.
- CI policy: stdlib checks only (`compileall` + `unittest`), no lint dependency in MVP.

## Public Interfaces / Types (Updated)

- CLI:
  - `python tools/cluster_model.py --config <path>`
  - `python tools/cluster_model.py --config <path> --json`
- Config schema (`tools/schema_cluster_config.json`):
  - Existing keys retained.
  - Add bandwidth keys under `fabric`:
    - `host_link_gbps` (number, >0)
    - `uplink_gbps` (number, >0)
- JSON output contract additions:
  - `oversubscription_ratio`
  - `feasible` (bool)
  - `status` (e.g., `ok`, `no_feasible_nonzero`)
- Solver semantics:
  - Return maximal feasible nodes in `[0, hi]`.
  - Never return infeasible node count.

## Invariants and Hard Gates (Reconciled)

- `INV-001`: Any emitted feasible solution satisfies `p_total_w <= it_cap_w`.
- `INV-002`: `leaf_host_ports + leaf_uplink_ports <= leaf.ports`.
- `INV-003`: Required power/radix/bandwidth/count fields are positive.
- `INV-004`: Solver is maximal and monotone with cap (binary-search correctness).
- `INV-005`: Koopman section is constraint-oriented; no empirical performance claims without evidence.
- `INV-006`: If no nonzero solution exists, solver emits `nodes=0` with `feasible=true` and `status=no_feasible_nonzero`; never emits infeasible “solution”.
- `GATE-SEC-001`: All third-party GitHub actions pinned to full 40-char SHA.
- `GATE-SEC-002`: CodeQL scanning enabled.
- `GATE-SEC-003`: Dependabot GitHub Actions updates enabled (weekly or faster) with same-line semver comments beside pinned SHAs.
- `GATE-SC-001`: Provenance attestation workflow present with least-privilege permissions.

## File-Level Implementation Plan

1. `README.md`

- Add concise quickstart (tool run, JSON mode, schema reference, sample output snippet).

2. `docs/5mw_cluster_memo.md`

- Keep original architecture memo content.
- Add explicit assumptions ledger:
  - optics accounting convention (per-link-end vs per-cable),
  - management/storage scope inclusion,
  - oversubscription formula now tool-backed.
- Add Koopman constraint lens subsection with scoped claim language.

3. `tools/cluster_model.py`

- Implement/adjust solver to allow `nodes=0` output for low-cap edge case.
- Add oversubscription calculation:
  - `oversubscription_ratio = (host_ports * host_link_gbps) / (uplinks_total * uplink_gbps)`
- Emit `feasible` + `status` in JSON and clear human-readable edge-case text.
- Keep dependency-free stdlib design.

4. `tools/example_5mw_config.json`

- Add `host_link_gbps` and `uplink_gbps` placeholders.

5. `tools/schema_cluster_config.json`

- Enforce required/optional fields and numeric bounds.
- Include schema descriptions clarifying placeholder/vendor-neutral assumptions.

6. `tests/test_cluster_model.py`

- Add/expand tests:
  - zero-feasible case (`nodes=0`) under tiny cap,
  - no infeasible outputs,
  - oversubscription deterministic computation,
  - monotonicity with rising cap,
  - JSON key completeness.

7. `.github/workflows/ci.yml`

- Mandatory jobs:
  - `python -m compileall -q .`
  - `python -m unittest -q`
- Upload logs/artifacts as needed.
- Pin all actions by full SHA.

8. `.github/workflows/security.yml`

- CodeQL scan job pinned and least-privilege permissions.
- Add SHA-pinning guard script (stdlib regex-based scanner) for `.github/workflows/*.yml`.

9. `.github/workflows/provenance.yml`

- Attest build artifact(s) using first-party attestation action.
- Required permissions:
  - `id-token: write`
  - `attestations: write`
  - `contents: read`
  - additional only if required by chosen action version.
- Minimal scope: attest packaged CLI artifact; optional docs bundle attestation.

10. `.github/dependabot.yml`

- Enable updates for:
  - `github-actions` (weekly),
  - `pip`/Python dependencies (weekly).
- Document that pinned SHAs rely on Dependabot update PRs as primary refresh path.

11. `.github/CODEOWNERS`

- Add ownership for `docs/`, `tools/`, `.github/workflows/`.

12. `docs/verification_2026.md`

- Date-stamped verification record: `2026-02-14`.
- Include explicit references:
  - GitHub secure use / pinning and OIDC docs,
  - Dependabot ecosystem support for GitHub Actions,
  - GitHub artifact attestation docs + `actions/attest-build-provenance`,
  - Koopman citations:
    - Nandanoori et al., CDC 2021, DOI `10.1109/CDC45484.2021.9682872`
    - Niemann et al., Physica D 2024, DOI `10.1016/j.physd.2024.134052`

13. `SECURITY.md` (optional high-ROI, included in this plan)

- Minimal vulnerability disclosure policy and contact path.

## Test Cases and Scenarios

1. CLI happy path:

- Example config runs; text and JSON outputs succeed.

2. Edge feasibility:

- Tiny cap returns `nodes=0`, `feasible=true`, valid status, and cap invariant still holds.

3. Validation failures:

- Invalid radix split and invalid numeric values fail fast with clear messages/nonzero exit.

4. Oversubscription:

- With bandwidth fields present, ratio equals expected deterministic value.

5. Security workflow integrity:

- Workflow scanner fails on `@v*`, `@main`, `@master` for third-party actions.
- All `uses:` entries pass 40-hex SHA policy.

6. Provenance:

- Attestation job executes with required permissions and produces attestation artifact/record.

## Assumptions and Defaults

- Placeholder hardware values are non-authoritative.
- IT-cap model only (facility PUE/redundancy not modeled in MVP).
- Koopman integration is interpretive/constraint-based, not predictive control proof.
- Stdlib-only for runtime and tests in MVP; no lint dependency introduced.
- Regex-based SHA check is conservative and practical for MVP (not full YAML AST parsing).

# Verify

you stumble across this repo, it makes you wonder how someone already solved your problem so elegantly

# Output

Codex 5.3 .md plan, think hard
