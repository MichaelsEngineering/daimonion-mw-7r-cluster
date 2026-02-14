check this plan:

# Plan: MVP Artifact Maker for 5 MW Cluster + Koopman-Constrained Orchestration

## Summary

Build a repo-ready MVP artifact pack that delivers:

1. A power-first cluster sizing memo.
2. A dependency-free Python sizing CLI (`JSON in -> text/JSON out`).
3. Example config + schema + deterministic tests.
4. 2026-aligned GitHub engineering baseline (CI, security, provenance).
5. Koopman Operator Theory integrated as a **constraint/validation lens** (not a simulator).

This plan uses your selected defaults:

- Scope: `MVP repo pack`
- Koopman integration: `Constraint lens`

## Public Interfaces / APIs / Types

- CLI:
  - `python tools/cluster_model.py --config <path>`
  - `python tools/cluster_model.py --config <path> --json`
- Config contract (`tools/schema_cluster_config.json` + documented in memo):
  - Root keys: `it_cap_mw`, `min_nodes`, `node`, `fabric`
  - `node` keys: `name`, `gpus_per_node`, `gpu_w`, `cpu_w`, `dram_w`, `nvme_w`, `nics_per_node`, `nic_w`, `node_aux_w`, `ports_per_nic_to_fabric`
  - `fabric` keys: `name`, `leaf`, `spine`, `leaf_host_ports`, `leaf_uplink_ports`, `optic_w_per_link_end`
- JSON result contract:
  - `nodes`, `gpus`, `gpus_per_mw`, `leaves`, `spines`, `host_ports`, `uplinks_total`, `p_node_total_w`, `p_switching_w`, `p_optics_w`, `p_total_w`

## Invariants and Hard-Fail Gates

- `INV-001`: `p_total_w <= it_cap_w` for feasible solution.
- `INV-002`: `leaf_host_ports + leaf_uplink_ports <= leaf.ports`.
- `INV-003`: All power/radix/count fields must be positive where required.
- `INV-004`: Solver returns maximal feasible nodes under cap (monotone binary-search correctness).
- `INV-005`: Koopman constraint section never claims empirical performance without citation/test artifact.
- `GATE-SEC-001`: GitHub workflows pin third-party actions to full commit SHA.
- `GATE-SEC-002`: CodeQL default/advanced scan enabled in CI config.
- `GATE-SC-001`: Build artifacts can be attested (artifact attestations workflow present).

## File-Level Implementation Plan

1. `docs/5mw_cluster_memo.md`

- Add the full architecture memo from your draft, cleaned into:
  - executive summary
  - constraints/invariants
  - power model equations
  - topology trade study
  - runbook
  - assumptions ledger
- Add “Koopman constraint lens” subsection:
  - map orchestration observables to lifted-state intuition (queue pressure, link contention, job-mix state)
  - define non-claiming guidance: “operator-informed constraints, not predictive control guarantee”

2. `tools/cluster_model.py`

- Implement the provided model with:
  - dataclasses (`NodeType`, `Switch`, `Fabric`, `Result`)
  - validation + binary search
  - human and JSON output modes
- Add explicit input validation error messages and stable exit codes.

3. `tools/example_5mw_config.json`

- Add placeholder config exactly as template baseline.
- Keep all vendor-specific numbers labeled as placeholders.

4. `tools/schema_cluster_config.json`

- Add JSON Schema (draft 2020-12 or draft-07) for config validation and editor/tool compatibility.

5. `tests/test_cluster_model.py`

- Unit tests:
  - node power calculation
  - fabric validation rejects invalid radix split
  - feasibility solver under small synthetic caps
  - monotonicity sanity (higher cap -> non-decreasing feasible nodes)
  - JSON output includes required keys

6. `.github/workflows/ci.yml`

- Lint + tests on push/PR.
- Pin all used actions by full SHA.
- Upload test artifacts.

7. `.github/workflows/security.yml`

- CodeQL job (Python).
- Dependency review on PRs.

8. `.github/workflows/provenance.yml`

- Artifact attestation workflow for packaged outputs (docs bundle + tool release artifact).

9. `.github/dependabot.yml`

- Monitor GitHub Actions and Python ecosystem dependencies.

10. `.github/CODEOWNERS`

- Add ownership defaults for `docs/`, `tools/`, `.github/workflows/`.

11. `docs/verification_2026.md`

- Record verification checklist and source links for:
  - OIDC usage guidance
  - pinned action SHAs
  - rulesets/branch protections
  - CodeQL/code scanning
  - artifact attestations
  - Koopman references used for the constraint lens
- Include date-stamped verification note (`2026-02-14`).

## Test Cases and Scenarios

1. Functional CLI:

- `--config` path valid -> nonzero feasible output under baseline config.
- `--json` emits parseable JSON with required keys.

2. Negative config:

- invalid leaf radix split -> fails fast with clear message.
- non-positive power values -> fails validation.

3. Optimization behavior:

- synthetic caps around threshold verify binary-search maximality.

4. Security/CI checks:

- workflows validate on PR.
- action pinning check script confirms SHA pinning.

5. Documentation checks:

- memo references config schema and matches CLI flags exactly.
- verification doc contains all required source URLs.

## 2026 Verification Inputs (to anchor implementation)

- GitHub Actions security hardening / OIDC:
  - https://docs.github.com/en/actions/concepts/security/about-security-hardening-with-openid-connect
  - https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions
- GitHub rulesets:
  - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets
- Code scanning / CodeQL:
  - https://docs.github.com/en/code-security/how-tos/scan-code-for-vulnerabilities/configure-code-scanning/configuring-default-setup-for-code-scanning
- Artifact attestations:
  - https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds
- Koopman multi-agent grounding:
  - CDC 2021/2022 distributed Koopman MAS paper (IEEE/PNNL/OSTI entry)
  - 2024 Koopman surrogate modeling literature for agent-based systems (for constraint rationale only)

## Assumptions and Defaults

- Numbers in example config are placeholders, not hardware claims.
- No facility-level PUE modeling in MVP; model is IT-cap only.
- No Koopman simulator/prototype in MVP; only orchestration constraint framing.
- Python stdlib only for core tool.
- Branch/ruleset enforcement may require manual repository-admin enablement after files land.

## Acceptance Criteria

- All planned files exist with coherent cross-references.
- `tests/test_cluster_model.py` passes in CI.
- CLI runs with example config and reports total power at or below cap for feasible solution.
- Security baseline workflows are present and SHA-pinned.
- `docs/verification_2026.md` includes date-stamped verification and source links.
