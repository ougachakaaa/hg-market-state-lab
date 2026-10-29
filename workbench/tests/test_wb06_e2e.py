"""Dense full-window acceptance and saved-output integrity; no market providers."""

import json
from pathlib import Path

from test_historical_return_g3 import backend
from wb06_e2e_example import TASK, discover, no_consent, run_case


def test_agent_candidate_full_window_results_and_historical_reads(tmp_path):
    draft = json.loads((TASK / "wb06" / "candidate.json").read_text(encoding="utf-8"))
    with backend() as (target, _, calls):
        complete = run_case(tmp_path, discover(tmp_path, target), draft)
        partial = run_case(tmp_path, discover(tmp_path, target), draft, missing=True)
        blocked = no_consent(tmp_path, target, draft)
    assert all(method == "GET" for method, _ in calls)
    assert complete["population"]["candidate_count"] > 4000
    assert complete["population"]["unavailable_count"] == 0
    assert partial["population"]["unavailable_count"] == 2
    assert partial["population"]["eligible_count"] == complete["population"]["eligible_count"] - 2
    for case in (complete, partial):
        assert case["plan"] == draft["research_plan"]
        assert case["execute_batch_calls"] == 1 and case["provider_calls"] == 0
        assert case["historical_result_still_readable"] is True
        assert case["gates_at_completion"] == {
            "G1": "PASS", "G2": "SKIPPED", "G3": "PASS", "G4": "PASS",
            "G5": "PASS", "G6": "SKIPPED"}
        ref = case["result_artifact"]
        assert (tmp_path / case["run_id"] / ref["stored_path"]).is_file()
        assert not Path(ref["stored_path"]).is_absolute()
    assert blocked["status"] == "BLOCKED" and blocked["intent_count"] == 0
