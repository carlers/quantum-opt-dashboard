"""Real unified Streamlit route must preserve candidate-only N50/100 boundary."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

UNIFIED = Path(__file__).resolve().parents[1] / "app.py"


def test_unified_water_resolution_selector_is_read_only_at_n100():
    app = AppTest.from_file(str(UNIFIED), default_timeout=120).run()
    assert not app.exception, app.exception
    control = next(s for s in app.selectbox if
                   s.label == "Research resolution (free candidates N)")
    control.set_value(100).run()
    assert not app.exception, app.exception
    assert "mvp_result" not in app.session_state
    assert not any(b.key == "mvp_run" for b in app.button)
    assert any(m.label == "Free candidates (N)" and str(m.value) == "100"
               for m in app.metric)
    assert any("NOT solved deployments" in str(w.proto) for w in app.warning)
