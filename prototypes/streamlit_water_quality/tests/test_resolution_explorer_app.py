"""Browser and provenance guards for additive research resolution selector."""
from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

WATER = Path(__file__).resolve().parents[1] / "app.py"


def _start():
    app = AppTest.from_file(str(WATER), default_timeout=120).run()
    assert not app.exception, app.exception
    return app


def _resolution(app):
    return next(s for s in app.selectbox if s.label == "Research resolution (free candidates N)")


def test_n20_is_default_and_preserves_existing_solver_gate():
    app = _start()
    assert _resolution(app).value == 20
    assert any(b.key == "mvp_run" for b in app.button)
    assert "mvp_result" not in app.session_state


def test_n50_and_n100_show_candidate_only_comparison_without_solver():
    app = _start()
    for n in (50, 100):
        _resolution(app).set_value(n).run()
        assert not app.exception, app.exception
        assert "mvp_result" not in app.session_state
        assert not [b for b in app.button if b.key == "mvp_run"]
        assert not [m for m in app.metric if m.label == "Original objective (min.)"]
        assert any(m.label == "Free candidates (N)" and str(m.value) == str(n)
                   for m in app.metric)
        assert any("NOT solved deployments" in str(w.proto) for w in app.warning)
        assert any("No cross-N solver timings" in str(c.proto) for c in app.caption)
        assert any("Cross-resolution source comparison" in h.value
                   for h in app.subheader)


def test_switch_away_from_certified_n20_never_relabels_its_result():
    app = _start()
    app.button(key="mvp_run").click().run()
    assert not app.exception, app.exception
    assert "mvp_result" in app.session_state
    n20_sha = app.session_state["mvp_result"]["fingerprint"]
    _resolution(app).set_value(50).run()
    assert not app.exception, app.exception
    assert "mvp_result" not in app.session_state
    assert not [b for b in app.button if b.key == "mvp_run"]
    _resolution(app).set_value(20).run()
    assert not app.exception, app.exception
    assert "mvp_result" not in app.session_state
    assert not [m for m in app.metric if m.label == "Original objective (min.)"]
    assert any(b.key == "mvp_run" for b in app.button)
