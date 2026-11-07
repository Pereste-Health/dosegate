import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(ROOT, "eval")
sys.path.insert(0, EVAL)
import human_agreement as ha  # noqa: E402

MANIFEST = os.path.join(EVAL, "labeling", "queue_manifest.json")
needs_data = pytest.mark.skipif(not os.path.exists(MANIFEST), reason="queue manifest not built")


def synthetic(tmp_path, *args):
    out = tmp_path / "labels.json"
    subprocess.run([sys.executable, os.path.join(EVAL, "labeling", "make_synthetic_labels.py"), "--out", str(out), *args], check=True, capture_output=True)
    return str(out)


def test_kappa_matches_hand_computation():
    pairs = [("a", "a")] * 20 + [("b", "b")] * 15 + [("a", "b")] * 5 + [("b", "a")] * 10
    po = 35 / 50
    pe = (25 * 30 + 25 * 20) / 2500
    assert ha.cohen_kappa(pairs, ["a", "b"]) == pytest.approx((po - pe) / (1 - pe))
    assert ha.cohen_kappa([("a", "a")] * 4, ["a", "b"]) is None
    assert ha.cohen_kappa([], ["a", "b"]) is None
    assert ha.cohen_kappa([("a", "a")] * 9 + [("a", "b")], ["a", "b"]) == pytest.approx(0.0)


def test_kappa_agrees_with_labels_py():
    from labels import kappa
    pairs = [("faithful", "faithful")] * 30 + [("misstates_order", "misstates_order")] * 6 + [("faithful", "misstates_order")] * 3 + [("unsupported_claim", "faithful")] * 2
    assert ha.cohen_kappa(pairs, ha.CATS) == pytest.approx(kappa(pairs))


def test_load_human_accepts_three_shapes_and_reports_invalid(tmp_path):
    rec = {"item_id": "q001", "label": "faithful"}
    for shape in ({"labels": [rec]}, [rec], {"q001": rec}):
        p = tmp_path / "labels.json"
        p.write_text(json.dumps(shape))
        assert ha.load_human(str(p)) == {"q001": rec}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"labels": [{"item_id": "q002", "label": "maybe"}, {"item_id": "q003", "label": None}]}))
    invalid = []
    assert ha.load_human(str(p), invalid) == {}
    assert invalid == [("q002", "maybe")]


@needs_data
def test_perfect_synthetic_agreement(tmp_path):
    manifest = json.load(open(MANIFEST))
    report = ha.build_report(manifest, ha.load_adopted(manifest), ha.load_human(synthetic(tmp_path, "--agreement", "1.0")))
    assert report["n_labeled"] == report["n_items"] == 193
    h2 = report["pooled"]["h2"]
    assert (h2["n"], h2["agree"], h2["kappa_three_labels"]) == (43, 43, pytest.approx(1.0))
    assert report["strata"]["h2_misstates_order"]["n"] == 9
    assert report["strata"]["h2_unsupported_claim"]["n"] == 4
    assert report["strata"]["h2_faithful"]["n"] == 30
    assert report["strata"]["pair"]["n"] == 16
    assert report["strata"]["open_model"]["n"] == 60
    assert report["strata"]["claude_claude-haiku-5-5"]["n"] == 46
    assert report["strata"]["claude_claude-sonnet-5-5"]["n"] == 28
    assert report["pooled"]["all_with_adopted_label"]["agree"] == 119
    assert report["disagreements"] == []
    assert report["strata"]["open_model"]["kappa_three_labels"] is None
    assert report["strata"]["open_model"]["adopted_label_varies"] is False
    assert report["strata"]["h2_misstates_order"]["error_type_agree"] is None
    assert len(ha.sentences(report, manifest)) == 6


@needs_data
def test_constant_stratum_kappa_is_zero_when_human_varies(tmp_path):
    manifest = json.load(open(MANIFEST))
    report = ha.build_report(manifest, ha.load_adopted(manifest), ha.load_human(synthetic(tmp_path, "--agreement", "0.8", "--seed", "5")))
    om = report["strata"]["open_model"]
    assert om["adopted_label_varies"] is False
    assert om["agree"] < om["n_with_adopted_label"]
    assert om["kappa_three_labels"] == pytest.approx(0.0)
    assert "0 by construction" in ha.sentences(report, manifest)[1] or report["pooled"]["h2"]["adopted_label_varies"]


@needs_data
def test_partial_synthetic_file(tmp_path):
    manifest = json.load(open(MANIFEST))
    human = ha.load_human(synthetic(tmp_path, "--agreement", "0.7", "--fraction", "0.5", "--seed", "3"))
    report = ha.build_report(manifest, ha.load_adopted(manifest), human)
    assert 0 < report["n_labeled"] < 193
    al = report["pooled"]["all_with_adopted_label"]
    assert al["n_labeled"] == al["n_with_adopted_label"] == len(set(human) & {it["id"] for it in manifest["items"] if it["stratum"] != "claude_free_daily"})
    assert al["agree"] + len(report["disagreements"]) == al["n_with_adopted_label"]
    assert -1.0 <= al["kappa_three_labels"] <= 1.0
    text = " ".join(ha.sentences(report, manifest))
    assert "labeled so far" in text
    assert f"{al['unsure']} of these {al['n_with_adopted_label']} labels unsure" in text


@needs_data
def test_empty_labels_file(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text(json.dumps({"labels": []}))
    manifest = json.load(open(MANIFEST))
    report = ha.build_report(manifest, ha.load_adopted(manifest), ha.load_human(str(p)))
    assert report["n_labeled"] == 0
    assert len(ha.sentences(report, manifest)) == 1
