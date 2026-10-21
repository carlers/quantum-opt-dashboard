# Restricted research-only preview: operator preflight and rollback gate

**Review stage:** 2026-10-21. **Status: unmerged DRAFT; NOT live Cloud certification.**
Root preview integration [DRAFT #125](https://github.com/carlers/quantum-opt-dashboard/pull/125);
follow-up review notice DRAFT stacked on that integration HEAD. Tracked in
[#108](https://github.com/carlers/quantum-opt-dashboard/issues/108),
[#16](https://github.com/carlers/quantum-opt-dashboard/issues/16),
[#105](https://github.com/carlers/quantum-opt-dashboard/issues/105), and
[#126](https://github.com/carlers/quantum-opt-dashboard/issues/126).

## Actual service scope and why a public branch merge is not safe yet

The GitHub repository `carlers/quantum-opt-dashboard` is **public**.
Official Streamlit Community Cloud documentation says apps deployed from a public
GitHub repository are **public by default**; an owner/developer can change
"Who can view this app" in the Streamlit Community Cloud app **Settings →
Sharing** to **Only specific people can view this app**.
Reference: https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app

**We have NOT authenticated to Streamlit Community Cloud workspace, accessed
actual privacy settings, confirmed who owns the app, or confirmed exact
repository/branch/entrypoint bindings of the persistent preview.** The
listed historical preview URL
`https://quantum-opt-dashboard-55zt76rpzbn2n3dltqfgis.streamlit.app/`
was present in the review docs, but its live private/public status is
**unverified**. The production URL is a different app and must never be changed
as a shortcut. The connected GitHub plugin cannot set Streamlit app sharing,
and the public webpage reader could not access the dynamic app to confirm it.

Updating the protected `preview` branch can immediately redeploy its bound
Community Cloud app **without a separate GitHub Actions deployment workflow**.
Successful GitHub CI therefore does not authorize merging code into the branch.
There are no current code changes to main, preview or the standalone source
paper/notebook/5,417-site GeoJSON/S4 factors. The extra all-routes notice is
scientific communication, **not** access control or proof of data rights.

## Mandatory operator attestation BEFORE any preview merge

- [ ] From https://share.streamlit.io, sign in to the actual app's workspace;
  confirm app **owner/admin**, its repository, branch, and main entrypoint
  (**expected**: `carlers/quantum-opt-dashboard`, `preview`,
  `prototypes/unified_dashboard/app.py`). Do not rely solely on historical
  documentation or a guessed app URL.
- [ ] In that specific app's **Settings → Sharing**, select
  **Only specific people can view this app** and save; verify approved viewer
  identities and remove unneeded invitations. A private viewer may access
  workspace analytics; review permissions as part of consent.
- [ ] Validate privacy as an **unauthenticated/logged-out browser user**:
  restricted app content, candidate locations and original evidence ZIP
  must not load until authentication/invitation. Document observation time,
  reviewer and app URL without recording personal email addresses or secrets
  in the public repo. If app cannot be made private, **STOP**.
- [ ] Confirm **Python 3.12**, root `requirements.txt`, single unified
  `prototypes/unified_dashboard/app.py` entrypoint and designated app
  `preview` branch. Check Streamlit Cloud secrets/environment for
  `QOPT_REVIEW_BOUNDED_SCIP`: it must **NOT** be `1`.
  Original in-process SCIP remains default and is **not a per-user OS quota**.
  Require constrained access and agreed usage/CPU load policy. Never place
  secret values, tokens, private invitation lists or project credentials in
  GitHub issues, test archives or app logs.
- [ ] Verify proposed preview's **data-owner/rights-holder** permits the
  restricted, invited research group to access the committed derived
  5,417-feature GeoJSON and data source displays. Private sharing alone
  is NOT license clearance. If uncertain, **STOP and resolve [#126]**.
- [ ] Obtain explicit academic/adviser scope acknowledgement that the
  visible computational source uses notebook AHP weights and
  `d2_road_proximity`, NOT the manuscript's WorldPop D2 semantics or
  paper-score reproduction. The UI must label modeled one-hop vs global
  geometry and classical SA correctly, with no field deployment guidance.
- [ ] Review all PR #125 + follow-up draft CI on the **exact final HEAD**:
  installed Python 3.12, native SCIP full original pilot, source hash and LP
  structure, original separate cold source-checkout #96, actual local
  Chromium ZIP bytes for K5/K4, dual sessions, input validation and
  all four route notices. Record GitHub synthetic CI merge SHA separately
  from source HEAD. No ancestor-only "green" shortcuts.
- [ ] Independently decide merge, deployment, and rollback. A green PR and
  a broad intent to continue are not equivalent to proof of each condition.

## Only after all checks — staged restricted browser acceptance

- Open the exact restricted URL **authenticated as an approved reviewer**
  after merging under separate recorded owner approval.
- Confirm four pages and the research-only warning on every route.
  Original local N20/K5 SCIP only when clicked; inspect output selection
  `[0,1,3,6,7]`, actual LP ZIP and source fingerprint under current
  permitted usage limits.
- Switch to modeled all-15-fixed global graph: do not label its exact
  enumeration as SCIP or as real measured RF/backhaul links; ensure
  stale local ZIP is invalidated on mode change. Research SA is classical.
- Record only public-safe SHA/proof metadata; do not publish private
  station coordinates, external AHP questionnaires or signed-in URLs.
  Tests on ephemeral loopback Chromium are NOT evidence of Cloud acceptance.
- Roll back by an explicitly reviewed revert restoring pre-merge
  protected `preview` commit
  `0fa4354c6182d70674ce46ffa68870796055ba75`
  (or owner-approved new clean target), and verify the persistent app
  source/branch and private-sharing setting again. **Do not blindly force-push**.
  Preserve original notebook/source-science DRAFT #96 separately.

## Scientific and operational nonclaims

The original *local one-hop* N20/K5 study computationally finds
**1,077 feasible / 15,504** assignments, selected candidate indices
`[0,1,3,6,7]`, under the historical source assumptions. An
**exploratory** 15-fixed globally connected geometric scenario has
**860 feasible / 15,504**; the feasible domains are different. The
paper's AHP/GIS/D2 input parity, real telemetry RF/dissolved oxygen/
current/backhaul, per-user cgroup resident RAM and quantum hardware
advantage are **not established**. Two observed binary64 coefficient
SHA variants must not be treated as byte-equivalent. Existing 14-day
unsigned GitHub evidence artifacts are NOT a durable scientific archive.

This gate **does not** modify the original source science, author manuscript,
paper/GeoJSON/S4 factors, access settings or protected deployment branches.
No automatic merge, Cloud deployment or archive upload is authorized
by this document.
