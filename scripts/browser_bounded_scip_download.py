"""Two real LOCAL Chromium sessions solve via opt-in bounded SCIP and download ZIPs.

Ephemeral 127.0.0.1 Streamlit only. This is not permanent Cloud browser
acceptance, signed provenance, physical lake measurement or hostile-user sandbox.
No source GeoJSON or downloaded ZIP is included in the uploaded CI artifact.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import closing
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
from zipfile import ZipFile

from playwright.async_api import async_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "prototypes/unified_dashboard/app.py"
DATA = ROOT / "problems/water_quality/data/LDB_centroids_clean.geojson"
BEST = [0, 1, 3, 6, 7]
DOWNLOAD_LABEL = "Download experiment, verified result and actual SCIP LP (.zip)"
RUN_LABEL = "Find monitoring locations (SCIP)"
SUCCESS_LABEL = "SCIP certified an optimal solution for the original local formulation."


def _require(value: bool, reason: str) -> None:
    if not value:
        raise AssertionError("Issue108 local browser bounded SCIP ZIP: " + reason)


def _port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _health(server: subprocess.Popen, origin: str) -> None:
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        _require(server.poll() is None, "local Streamlit quit before healthcheck")
        try:
            with urlopen(origin + "/_stcore/health", timeout=2) as reply:
                if reply.status == 200 and b"ok" in reply.read().lower():
                    return
        except OSError:
            pass
        time.sleep(.4)
    raise TimeoutError("actual local Streamlit never reached health status")


def _check_download(contents: bytes, filename: str, original_instance) -> dict:
    from scip_lp_structure import certify_emitted_scip_lp

    _require(filename.startswith("water-mvp-") and filename.endswith(".zip"),
             "unexpected download filename")
    _require(0 < len(contents) < 2_000_000, "download empty or unexpectedly large")
    with ZipFile(BytesIO(contents)) as bundle:
        names = set(bundle.namelist())
        _require(names == {
            "SHA256SUMS.json", "model.json", "result.json",
            "actual_scip_model.lp", "selected_sites.csv",
        }, "actual browser ZIP missing/extra expected original science files")
        _require(all(bundle.getinfo(n).file_size < 350_000 for n in names),
                 "ZIP contains unexpectedly large scientific member")
        hashes = json.loads(bundle.read("SHA256SUMS.json"))
        original_model = json.loads(bundle.read("model.json"))
        result = json.loads(bundle.read("result.json"))
        _require(set(hashes["files_sha256"]) == (names - {"SHA256SUMS.json"}),
                 "actual download checksum manifest has wrong files")
        for name, expected in hashes["files_sha256"].items():
            _require(sha256(bundle.read(name)).hexdigest() == expected,
                     "downloaded archive SHA mismatch for " + name)
        _require(hashes["source_geojson_sha256"] == original_model["dataset_sha256"],
                 "source-GeoJSON digest does not match active model fingerprint")
        _require(result["model_fingerprint_sha256"] ==
                 original_model["model_fingerprint_sha256"],
                 "download evidence is not bound to visible formulation")
        _require(result["scip_status"] == "optimal"
                 and result["scip_optimal_proven"] is True,
                 "browser did not download exact SCIP-certified original result")
        _require(result["independent_audit"]["selected_local_positions"] == BEST,
                 "downloaded browser original N20/K5 optimal sites mismatch")
        raw_lp = bundle.read("actual_scip_model.lp")
        certificate = certify_emitted_scip_lp(original_instance, raw_lp)
        _require(certificate["budget_equal_K_verified"] is True
                 and certificate["each_original_local_one_hop_verified"] is True
                 and certificate["original_scip_lp_sha256"] ==
                 hashes["files_sha256"]["actual_scip_model.lp"],
                 "downloaded original SCIP LP differs from source parent instance")
        return {
            "filename": filename,
            "downloaded_zip_sha256": sha256(contents).hexdigest(),
            "original_lp_sha256": sha256(raw_lp).hexdigest(),
            "fingerprint_sha256": original_model["model_fingerprint_sha256"],
            "original_source_sha256": original_model["dataset_sha256"],
            "selected_local_indices": BEST,
            "independent_source_lp_structure_verified": True,
            "browser_receipt_from_actual_click": True,
        }


async def _exercise(origin: str) -> list[tuple[bytes, str]]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            contexts = [
                await browser.new_context(
                    viewport={"width": 1440, "height": 900}, accept_downloads=True
                ) for _ in range(2)
            ]
            try:
                pages = [await ctx.new_page() for ctx in contexts]
                sockets = [[], []]
                for page, ws in zip(pages, sockets):
                    page.on("websocket", lambda obj, collector=ws: collector.append(obj))
                await asyncio.gather(*(
                    page.goto(origin, wait_until="domcontentloaded", timeout=60000)
                    for page in pages
                ))
                await asyncio.gather(*(
                    expect(page.get_by_role("heading", name="Water-quality sensor placement",
                                            exact=True)).to_be_visible(timeout=90000)
                    for page in pages
                ))
                _require(all(sockets) and sockets[0][0] is not sockets[1][0],
                         "two distinct live browser/Streamlit WebSockets absent")
                for page in pages:
                    _require(await page.locator('[data-testid="stException"]').count() == 0,
                             "exception before actual solver click")
                    await expect(
                        page.get_by_role("button", name=RUN_LABEL)
                    ).to_be_visible(timeout=90000)
                # Actions initiated concurrently in two genuinely separate browser contexts.
                # Does not assume SCIP optimization times overlap at the OS level.
                await asyncio.gather(*(
                    page.get_by_role("button", name=RUN_LABEL).click(timeout=30000)
                    for page in pages
                ))
                await asyncio.gather(*(
                    expect(page.get_by_text(SUCCESS_LABEL, exact=False))
                    .to_be_visible(timeout=150000)
                    for page in pages
                ))
                outputs = []
                for page in pages:
                    _require(await page.locator('[data-testid="stException"]').count() == 0,
                             "exception after actual original bounded SCIP run")
                    async with page.expect_download(timeout=60000) as download_info:
                        await page.get_by_role("button", name=DOWNLOAD_LABEL).click(
                            timeout=30000
                        )
                    download = await download_info.value
                    downloaded_path = await download.path()
                    _require(downloaded_path is not None,
                             "browser did not materialize actual Streamlit ZIP download")
                    outputs.append((Path(downloaded_path).read_bytes(),
                                    download.suggested_filename))
                return outputs
            finally:
                await asyncio.gather(*(ctx.close() for ctx in contexts))
        finally:
            await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _require(not args.output.exists(), "refuse overwriting prior evidence")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    server_log = args.output.parent / "local-bounded-browser-streamlit-server.log"
    port = _port()
    origin = f"http://127.0.0.1:{port}"
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(APP),
        "--server.headless=true", "--server.address=127.0.0.1",
        f"--server.port={port}", "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]
    with server_log.open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
            env={**os.environ, "QOPT_REVIEW_BOUNDED_SCIP": "1",
                 "OPENBLAS_NUM_THREADS": "1",
                 "OMP_NUM_THREADS": "1",
                 "MKL_NUM_THREADS": "1"},
        )
        try:
            _health(server, origin)
            raw_outputs = asyncio.run(_exercise(origin))
            _require(len(raw_outputs) == 2, "two actual browser ZIPs not observed")
            from model import NOTEBOOK_WEIGHTS, load_data, make_instance
            instance, simulated = make_instance(load_data(DATA), NOTEBOOK_WEIGHTS, 20, 5)
            _require(not simulated, "original source reference was simulated")
            receipts = [_check_download(blob, filename, instance)
                        for blob, filename in raw_outputs]
            source_head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
            ).strip()
            report = {
                "schema_version": 1,
                "kind": "LOCAL_TWO_BROWSER_CLICKS_OPTIN_BOUNDED_ORIGINAL_SCIP_ZIP",
                "source_pr_head_sha": os.getenv("PR_HEAD_SHA"),
                "actual_git_checkout_sha": source_head,
                "contexts": 2,
                "separate_live_websocket_contexts": True,
                "two_browser_solve_buttons_clicked_concurrently": True,
                "local_ephemeral_streamlit_worker_env_review_only": True,
                "successful_actual_browser_zip_download_count": 2,
                "receipts": receipts,
                "limitations": [
                    "Not the deployed Streamlit Cloud preview or production URL",
                    "Browser clicks launched concurrently; simultaneous OS optimization not established",
                    "No hostile qualified module or process-cache injection tested",
                    "No authentication/fair quotas, cgroup resident RAM, external signature",
                    "No original paper AHP/D2 parity, physical lake monitoring or quantum claim",
                ],
            }
            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8")
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)


if __name__ == "__main__":
    main()
