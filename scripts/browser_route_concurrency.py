"""Observe two overlapping REAL browser contexts against an ephemeral local Streamlit.

This is a bounded navigation regression, NOT malicious import-process isolation,
a production Cloud acceptance check, or an external authentication signature.
No SCIP solve, OpenJij sample, download-button click, or original data rewrite.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import closing
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

from playwright.async_api import async_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "prototypes/unified_dashboard/app.py"
ROUTES = {
    "water": ("Water-quality placement", "Water-quality sensor placement"),
    "custom": ("Configure another problem", "Configurable Optimization Workbench"),
    "research": ("QUBO and classical SA", "QUBO and classical annealing"),
    "about": ("About the research", "About the scientific workbench"),
}


def _port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _await_health(process: subprocess.Popen, address: str, timeout: float = 90) -> None:
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if process.poll() is not None:
            raise RuntimeError("Local Streamlit server exited during startup")
        try:
            with urllib.request.urlopen(address + "/_stcore/health", timeout=2) as reply:
                if reply.status == 200 and b"ok" in reply.read().lower():
                    return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.5)
    raise TimeoutError("Ephemeral local Streamlit healthcheck did not succeed")


async def _await_title(page, route: str) -> None:
    label = ROUTES[route][1]
    await expect(page.get_by_role("heading", name=label, exact=True)).to_be_visible(
        timeout=60000
    )
    # The global entrypoint notice must remain visible on every page for
    # genuine separate WebSocket/Chromium sessions, not just in AppTest.
    await expect(
        page.get_by_text("Research-only computational prototype", exact=False)
    ).to_be_visible(timeout=60000)
    # Streamlit exception element is an application error, not a friendly error
    # page or transient blank WebSocket screen.
    assert await page.locator('[data-testid="stException"]').count() == 0


async def _navigate(page, route: str) -> None:
    label = ROUTES[route][0]
    nav = page.get_by_test_id("stSidebarNav").get_by_text(label, exact=True)
    await expect(nav).to_be_visible(timeout=60000)
    await nav.click(timeout=30000)
    await _await_title(page, route)


async def _exercise(address: str) -> dict:
    """Two distinct isolated browser contexts, each with its own Streamlit socket."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            a_context = await browser.new_context(viewport={"width": 1440, "height": 900})
            b_context = await browser.new_context(viewport={"width": 1440, "height": 900})
            try:
                a = await a_context.new_page()
                b = await b_context.new_page()
                a_sockets, b_sockets = [], []
                a.on("websocket", lambda ws: a_sockets.append(ws))
                b.on("websocket", lambda ws: b_sockets.append(ws))
                await asyncio.gather(
                    a.goto(address, wait_until="domcontentloaded", timeout=60000),
                    b.goto(address, wait_until="domcontentloaded", timeout=60000),
                )
                await asyncio.gather(_await_title(a, "water"), _await_title(b, "water"))
                pairs = [
                    ("custom", "research"),
                    ("about", "water"),
                    ("research", "custom"),
                    ("water", "about"),
                ]
                observations = [{"a": "water", "b": "water"}]
                for a_route, b_route in pairs:
                    # Both WebSocket-connected ScriptRunner sessions remain live
                    # while their navigation actions happen concurrently.
                    await asyncio.gather(
                        _navigate(a, a_route),
                        _navigate(b, b_route),
                    )
                    assert await a.locator('[data-testid="stException"]').count() == 0
                    assert await b.locator('[data-testid="stException"]').count() == 0
                    assert await a.get_by_role("heading", name=ROUTES[b_route][1],
                                               exact=True).count() == (1 if a_route == b_route else 0)
                    assert await b.get_by_role("heading", name=ROUTES[a_route][1],
                                               exact=True).count() == (1 if a_route == b_route else 0)
                    observations.append({"a": a_route, "b": b_route})
                if not a_sockets or not b_sockets or a_sockets[0] is b_sockets[0]:
                    raise AssertionError("Two independent browser/WebSocket sessions not observed")
                return {
                    "contexts": 2,
                    "independent_streamlit_websocket_connections_observed": True,
                    "route_pairs": observations,
                }
            finally:
                await asyncio.gather(a_context.close(), b_context.close())
        finally:
            await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Do not overwrite prior browser audit evidence")
    port = _port()
    address = f"http://127.0.0.1:{port}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    server_log = args.output.parent / "local-browser-streamlit-server.log"
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(APP),
        "--server.headless=true",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]
    with server_log.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            _await_health(process, address)
            route_results = asyncio.run(_exercise(address))
            git_head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip()
            report = {
                "schema_version": 1,
                "kind": "LOCAL_EPHEMERAL_HEADLESS_CHROMIUM_MULTISESSION_NAVIGATION_ONLY",
                "source_pr_head_sha": os.environ.get("PR_HEAD_SHA"),
                "actual_git_checkout_sha": git_head,
                "browser": "Playwright Chromium, fresh isolated contexts",
                **route_results,
                "limitations": [
                    "No Cloud preview, deployed browser, physical lake validation or manuscript parity",
                    "No external network endpoint; ephemeral 127.0.0.1 Streamlit server",
                    "No adversarial qualified-module cache poisoning or proven hostile cross-session isolation",
                    "No actual download button click, SCIP solve, solver OS quota or signed result",
                    "Two simultaneous browser sessions are a liveness/isolation diagnostic, NOT a safety certification",
                ],
            }
            args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
