# Independent original N20 full-global source geometry and science/UX integration boundary

Date: 2026-10-19. Research review only. New source-only branch on draft PR #94. Original source science PR chain #68 -> #83 -> #84 -> #86 -> #89 -> #92 -> #93 -> #94 stays separate from unmerged UX PR chain #55 -> #77 -> #78. No merge or deploy is authorized by this experiment.

## Distinct mathematical model claims

Historical original N20/K5: 20 candidate sites, 15 existing stations, 5 new selected stations, source local one-hop adjacency. Connectivity can consist of disconnected clusters. The original mathematical reference has 1,077 locally feasible combinations and optimum indices [0,1,3,6,7] at -3.3012934918564643. Source notebook correctness does not mean manuscript AHP/D2 parity or field environmental validity.

New exploratory full-global requirement: all 15 existing stations AND all K selected new stations in one connected component, without invented fixed backhaul. Each direct edge joins two projected source sites only when the complete straight segment is strictly contained in the original source concave hull (ratio 0.05 with holes) and the projected distance is within original Dmax. Unlike the archived local notebook, the graph explicitly derives fixed-to-fixed links. These are modeled geometric links, NOT measured RF or proven communications.

## Preexisting UX PR #78 outcome to independently challenge

- All 15 original fixed stations and 20 original candidates form a 35-vertex modeled graph.
- Direct geometric edges: 11 candidate/candidate; 34 candidate/fixed; 17 fixed/fixed.
- Entire 35-vertex possible graph: 8 connected components, 7 of which are isolated optional candidate sites.
- Full all-fixed modeled-network K5 feasible: 860 of 15,504 candidate sets.
- Ordered K5 feasible membership SHA: 3ec652e943e26d7aa67ba71203dba6c5413a88a47dc4f24a2428a49c171bbc40.
- Global-mode mathematical optimum: [0,1,3,6,7], same original score -3.3012934918564643.
- This is not the earlier 110-feasible S2 subset connectivity scenario.

These are review canaries, not presumed results of the new independent branch. The independent CI must actually reproduce them.

## Independent science code without UX import

New scripts/n20_full_global_source_geometry.py directly reads the pinned 5,417-point GeoJSON, independently checks the original cold notebook with SCIP and the raw-source local geometry audit, and builds a NEW explicit 35-site graph including free/free, free/fixed and fixed/fixed links. Every free/free neighbor and every individual free/fixed link is compared with the independent local raw geometry reconstruction. The entire source full-global graph does not come from the UX module.

A separately implemented union-find over mandatory all-fixed plus only selected new nodes checks all 15,504 subsets, hashes the ordered feasible memberships and minimizes the exact rational objective from original binary64 coefficient bytes (fractions.Fraction). A second optimizer-independent BFS plus integer-scaled objective proof in scripts/bounded_result_attestation.py must match the union-find feasible set SHA, count and selected optimum. Current global model is explicitly exploratory and solver_backend is exact_enumeration, not a fabricated SCIP solve or LP.

The science graph digest is the SHA-256 of the minimal complete edge payload. The UX graph fingerprint hashes a DIFFERENT record with source site, hull and Dmax metadata. Their hash strings are not directly comparable. The shared Shapely/GEOS concave-hull engine remains an independence limitation; neither graph source independently validates real lake shoreline, RF, backhaul, lake currents or water-quality sensor coverage.

## Future cross-stack integration, contingent on owner review

Current science chain is able to verify historical original-source notebook/SCIP/GeoJSON/S4 and proof bounded mathematics, classify source versus exploratory runs, and prevent cache reuse when exact model inputs change. UX PR #78 has an actual Streamlit two-mode interface and modeled source graph and export pipeline. They have separate unmerged ancestry. This draft does NOT import/rebase/cherry-pick/merge UX code into the science branch.

The next separate review-only integration PR should use a human-reviewed ancestry and source-of-truth decision before changes. The backend must produce a server-compiled complete model and actual graph, solver status and selected sites, and generate a fingerprint for exactly that run. Then independent attestation precedes rendering map/results/ZIP/CSV. Topology, weights, dataset, D2 criterion, sites, K, Dmax, hull or solver change must invalidate prior run results and exports. Exact model identity is mandatory: the posthoc four-coefficient N20 numerical diagnostic envelope in PR #94 cannot authorize cache reuse or make differing exact scored objectives identical. UI must label historical local source calculation, exploratory global optimum, manuscript parity blocked and physical radio/environmental validity blocked separately.

Full integration acceptance requires actual Streamlit AppTest with real backend data, run/graph/LP/status tamper tests, honest timeout states and exact-head original source cold scientific gates. Neither successful standalone UX CI nor this source-only global graph proof is joint end-to-end integration evidence. External author AHP judgment forms, source WorldPop GIS provenance, shoreline with island holes, calibrated RF/backhaul and DO/current field records remain unavailable under Issue #87. The owner's original source notebook and manuscript are not to be rewritten or silently corrected.

Next steps: run real cold source/SCIP/S4 plus this independently derived global graph proof in a separate CI; inspect exact graph/feasible SHA/score evidence and publish only observed results, update Issues #88 and #91; leave all PRs draft and unmerged, with no preview/main/production changes or unsupported field claims.
