# Two-link Streamlit Community Cloud setup

**Goal:** exactly **one production app URL** and **one persistent preview app URL**, both backed by this GitHub repo, with no per-PR deployment or additional hosting service.

## Deployment contracts

| | Production (already deployed, unchanged) | Preview (owner-created Cloud app; runtime smoke pending) |
|---|---|---|
| Streamlit app | [Existing water-quality pilot](https://v3wzqpbn8w6nmdgkxh5kum.streamlit.app/) | [Integrated MVP preview](https://quantum-opt-dashboard-55zt76rpzbn2n3dltqfgis.streamlit.app/) |
| GitHub repository | `carlers/quantum-opt-dashboard` | `carlers/quantum-opt-dashboard` |
| **Branch** | `plugin-water-streamlit-pilot` | **`preview`** (permanent staging branch) |
| Main entrypoint | `prototypes/streamlit_water_quality/app.py` | **`prototypes/unified_dashboard/app.py`** |
| Python | Existing production setting (do not change) | **3.12** |
| Purpose | Public stable pilot; changes only with owner approval | Integrated research workbench; receives tested work in progress |

**The existing public main link does not mean the GitHub default `main` branch.** The actual deployed production pilot tracks the separate `plugin-water-streamlit-pilot` branch; GitHub `main` still has early scaffolding and is not the current live Streamlit app. Do not switch production's tracked branch until the owner approves a real release.

## Preview app created — original setup details (for recovery)

1. Go to https://share.streamlit.io/ and sign in with GitHub. Choose the `carlers` workspace if Streamlit asks.
2. Choose **Create app → Yup, I have an app**.
3. Enter **repository `carlers/quantum-opt-dashboard`**, **branch `preview`**, **main file `prototypes/unified_dashboard/app.py`**. Or choose **Paste GitHub URL** and paste `https://github.com/carlers/quantum-opt-dashboard/blob/preview/prototypes/unified_dashboard/app.py`. The app path is relative to repo root.
4. In **Advanced settings**, select **Python 3.12**. No app secrets are required by these committed synthetic/reference example workflows. Do not copy production secrets without specific need and approval.
5. Optional: choose a memorable subdomain containing `quantum-opt-dashboard-preview` **if available** (not reserved or verified). Otherwise accept the URL that Community Cloud assigns.
6. Deploy and open the app. **Owner reported the preview URL above on 2026-10-18**. The next check is to verify the app has successfully built and all four pages work in a real browser.

Community Cloud deploys different apps from the same repo independently. Once deployed, committing to its tracked `preview` branch automatically updates **only the preview app**. Committing to `plugin-water-streamlit-pilot` affects **only production**. You do not need a new Streamlit app for every PR. Changes to requirements trigger slower environment rebuilds.

Official docs:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies

## Day-to-day development

- Implement and validate changes on focused feature/PR branches. Use the scientific fast CI and UI tests already defined.
- When ready for preview, bring the reviewed code to `preview`; GitHub/Streamlit automatically refresh the **same preview URL**. Do not push every unverified experimental run to preview. The working tree can continue to evolve; tests and source/model fingerprints are preserved.
- Review the preview on desktop and mobile. Verify exact N20 SCIP solution, general synthetic editor, historical N20 QUBO, bounded classical SA, correct independent audits and downloadable source/LP evidence.
- When accepted, open/review a PR for release into `main` (the code integration branch), and separately decide whether to switch/upgrade the production Streamlit app. **Neither occurs automatically.**
- Continue to refer to `preview` as a **testing site**, not scientific publication certification. Short-lived GitHub Actions artifacts are not long-term experiment archives.

## Constraints

There is currently **no Streamlit Community Cloud deployment tool connected to this conversation**. The owner created the second app and supplied its URL, but successful Cloud startup and runtime behavior have **not been independently verified** here. The repo is public, so avoid uploading restricted data. Be careful not to upload real restricted data to a public research preview.

Community Cloud has shared resource limits; SCIP and OpenJij may run slower or cause memory pressure than CI. Check actual preview resource behavior before promoting a release.

**Preview app URL (owner-provided 2026-10-18):** https://quantum-opt-dashboard-55zt76rpzbn2n3dltqfgis.streamlit.app/

**Production app URL (unchanged):** https://v3wzqpbn8w6nmdgkxh5kum.streamlit.app/

**Staging verification:** Preview URL has been supplied, but page loading, numerical solves and downloads have not yet been browser-verified by the assistant. Opening the link is the next acceptance step.
