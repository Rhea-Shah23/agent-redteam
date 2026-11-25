import json

import pytest

from redteam.scoreboard import render, save_model, summarize, write_markdown


def r(attack, cls, config, success):
    return {"attack_id": attack, "cls": cls, "config": config, "success": success}


RESULTS = (
    [r("a1", "spend_limit", "baseline", s) for s in (True, True, False)]
    + [r("a1", "spend_limit", "scoped_creds", False)] * 3
    + [r("a2", "spend_limit", "baseline", False)] * 3
    + [r("a2", "spend_limit", "scoped_creds", False)] * 3
    + [r("e1", "prompt_extraction", "baseline", False)] * 3
)


def cell(summary, attack, config):
    return next(c for c in summary["cells"] if c["attack"] == attack and c["config"] == config)


def test_summarize_counts_successes_per_attack_and_config():
    s = summarize(RESULTS, "m")
    assert (cell(s, "a1", "baseline")["successes"], cell(s, "a1", "baseline")["trials"]) == (2, 3)
    assert cell(s, "a1", "scoped_creds")["successes"] == 0
    assert len(s["runs"]) == len(RESULTS)


def test_render_class_rows_pool_attacks_and_formats_rates():
    md = render([summarize(RESULTS, "m")])
    # spend_limit has two attacks x 3 trials on baseline = 6 trials, 2 successes
    assert "| spend_limit | 2 | 2/6 (33%) | 0/6 (0%) |" in md
    assert "| **all** | **3** | **2/9 (22%)** | **0/6 (0%)** |" in md


def test_missing_config_cell_renders_as_dash():
    md = render([summarize(RESULTS, "m")])
    assert "| e1 | prompt_extraction | 0/3 (0%) | - |" in md


def test_one_section_per_model():
    md = render([summarize(RESULTS, "model-a"), summarize(RESULTS, "model-b")])
    assert md.index("## model-a") < md.index("## model-b")


def test_class_rows_follow_the_order_in_attack_py():
    # spend_limit comes before prompt_extraction in CLASSES, whatever the input order
    md = render([summarize(RESULTS, "m")])
    assert md.index("| spend_limit | 2 |") < md.index("| prompt_extraction | 1 |")


def test_save_and_rebuild_from_files(tmp_path):
    save_model(RESULTS, "m1", tmp_path)
    save_model(RESULTS, "m2", tmp_path)
    assert json.loads((tmp_path / "m1.json").read_text())["model"] == "m1"
    md = write_markdown(tmp_path).read_text()
    assert "## m1" in md and "## m2" in md


def test_report_with_no_saved_results_is_a_clear_error(tmp_path):
    with pytest.raises(SystemExit, match="no saved results"):
        write_markdown(tmp_path / "nothing-here")
