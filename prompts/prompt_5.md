Make these edits and return a new plan:
Short answer
Plan is coherent and shippable. Two concrete fixes are required to make your invariants and acceptance criteria internally consistent: (1) define “no feasible solution” behavior in the solver (0 nodes vs hard-fail), and (2) reconcile SHA pinning with Dependabot alerts and update strategy. The rest is additive.

Key issues and corrections

1. Solver feasibility semantics (currently underspecified)
   Your invariants say `p_total_w <= it_cap_w` for a feasible solution and “solver returns maximal feasible nodes”. That implies one of these must be true when the cap is too small for even 1 node + minimal fabric:

Option A (recommended): allow `nodes = 0` as a valid feasible result and still maximize nodes.
Option B: hard-fail with a nonzero exit code and a clear message (“no feasible configuration under cap”).

Do not do “return min_nodes even if it violates cap”, because it breaks INV-001 and the acceptance criterion (“reports total power at or below cap for feasible solution”).

2. Oversubscription is referenced in the memo but not representable in the config/tool
   Right now the fabric model is pure “ports and counts”. If you want any claim about oversubscription, the tool should compute it deterministically from config. Minimal change:

* Add to config (optional but recommended):

  * `host_link_gbps` (or per-NIC speed)
  * `uplink_gbps`
* Output:

  * `oversubscription_ratio = (H * host_link_gbps) / (uplinks_total * uplink_gbps)`

If you keep the tool port-only, the memo must treat oversubscription qualitatively or as an external calculation.

3. SHA pinning gate vs Dependabot alerts and update mechanism
   Your SHA pinning gate is aligned with GitHub’s own “secure use” guidance (pin actions to full-length commit SHA). ([GitHub Docs][1])
   But GitHub also notes that Dependabot alerts do not get created for actions pinned to SHAs. ([GitHub Docs][1])

Implication for your plan:

* Keep `GATE-SEC-001` (SHA pinning) as-is.
* Make Dependabot version updates for GitHub Actions non-optional, because it becomes your primary update signal for pinned SHAs. GitHub docs explicitly cover Dependabot support/caveats for GitHub Actions, including `owner/action@<commit>` and comment-updating behavior. ([GitHub Docs][2])

Concrete plan edit: add a gate like

* `GATE-SEC-003`: Dependabot Actions updates enabled (schedule <= weekly) and workflows include a same-line comment with semver tag for readability.

4. Provenance workflow details (tighten to an actual primitive)
   Artifact attestation is feasible today with first-party actions. The repo `actions/attest-build-provenance` exists and documents required permissions. ([GitHub][3])
   GitHub Docs also describes required permissions for attestations and related actions like `actions/attest-sbom@v2`. ([GitHub Docs][4])

Concrete plan edit for `provenance.yml`:

* Ensure job permissions include `id-token: write` and `attestations: write` (plus whatever that specific action requires, e.g. `contents: read` and potentially `artifact-metadata: write`). ([GitHub][3])
* Decide scope: attest the built tool artifact (zip/tar) and optionally the docs bundle. Keep it minimal.

5. CI “lint” vs “stdlib only”
   If you want strict stdlib for the Python tool and tests, you can still run a robust CI without adding lint dependencies:

* `python -m compileall -q .`
* `python -m unittest -q`

If you insist on linting, it becomes a dependency decision (ruff/flake8). In that case, update the plan to explicitly allow dev deps and pin them, or keep lint out of MVP.

6. “Action pinning check script” without YAML dependencies
   Stdlib has no YAML parser. If you want an enforcement check in CI without deps, implement a conservative regex scanner over `.github/workflows/*.yml` and fail on `uses: OWNER/REPO@v*` / `@main` / `@master` unless it matches a 40-hex SHA. This will be approximate but practical.

If you want correctness, accept a YAML dependency and pin it, or use an existing marketplace action that enforces SHA pinning (but then you also need to SHA-pin that action). ([GitHub][5])

7. Koopman references should be de-ambiguous in the plan
   You list “CDC 2021/2022 distributed Koopman MAS paper” and “2024 Koopman surrogate modeling literature”. Replace these with explicit citations in `docs/verification_2026.md` (title, venue, DOI/arXiv).

Two concrete anchors you can cite without overclaiming:

* Nandanoori et al., “Data-driven Distributed Learning of Multi-agent Systems: A Koopman Operator Approach”, CDC 2021, DOI present. ([ACM Digital Library][6])
* Niemann et al., “Koopman-based surrogate models for multi-objective optimization of agent-based systems”, Physica D (2024), DOI 10.1016/j.physd.2024.134052. ([Heriot-Watt Research Portal][7])

Small additions that improve the repo pack (optional but high ROI)

* `README.md`: 10 lines of “what this is”, quickstart commands, config schema link, sample output.
* `LICENSE` (MIT/BSD-2-Clause).
* `SECURITY.md`: minimal disclosure text (even if it’s “best effort”).
* Add to memo: a clear “assumptions ledger” including whether optics power is per-link-end vs per-cable, and whether management networking is in-scope.

Concrete edits to your plan text (drop-in)

* Add to “Invariants and Hard-Fail Gates”:

  * `INV-006`: Solver returns `nodes=0` when no feasible nonzero solution exists, OR exits nonzero with message; never returns an infeasible “solution”.

* Add to “Public Interfaces / Types”:

  * Optional fabric bandwidth fields to enable oversubscription calculation, or explicitly state “tool does not compute oversubscription”.

* Add to “Security/CI checks”:

  * Note that SHA-pinning reduces Dependabot alerts coverage; require Dependabot Actions updates as compensation. ([GitHub Docs][1])

Verify

Local

* `python -m compileall -q .`
* `python -m unittest -q`
* `python tools/cluster_model.py --config tools/example_5mw_config.json`
* `python tools/cluster_model.py --config tools/example_5mw_config.json --json | python -m json.tool`

GitHub

* Confirm workflows use least-privilege `permissions:` and SHA-pinned `uses:` lines. ([GitHub Docs][1])
* Confirm attestation workflow has required permissions and uses the first-party attestation action. ([GitHub][3])

[1]: https://docs.github.com/en/actions/reference/security/secure-use "Secure use reference - GitHub Docs"
[2]: https://docs.github.com/code-security/dependabot/ecosystems-supported-by-dependabot/supported-ecosystems-and-repositories?utm_source=chatgpt.com "Dependabot supported ecosystems and repositories"
[3]: https://github.com/actions/attest-build-provenance?utm_source=chatgpt.com "actions/attest-build-provenance"
[4]: https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds?utm_source=chatgpt.com "Using artifact attestations to establish provenance for builds"
[5]: https://github.com/marketplace/actions/ensure-sha-pinned-actions?utm_source=chatgpt.com "GitHub Marketplace - Ensure SHA Pinned Actions"
[6]: https://dl.acm.org/doi/10.1109/CDC45484.2021.9682872?utm_source=chatgpt.com "Data-driven Distributed Learning of Multi-agent Systems"
[7]: https://researchportal.hw.ac.uk/en/publications/koopman-based-surrogate-models-for-multi-objective-optimization-o/?utm_source=chatgpt.com "Koopman-based surrogate models for multi-objective ..."

# Output 

a new plan that incorporates the changes