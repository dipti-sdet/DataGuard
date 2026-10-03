"""Every planted bug must be CAUGHT by at least its documented detector checks."""
import pytest

from dataguard.bugs import BUGS
from dataguard.runner import run_checks


@pytest.mark.parametrize("bug_id", list(BUGS))
def test_bug_is_detected(bug_id):
    failed = {cid for cid, (ok, _) in run_checks((bug_id,)).items() if not ok}
    assert failed, f"{bug_id} went undetected: no check failed"
    missing = set(BUGS[bug_id]["detectors"]) - failed
    assert not missing, f"{bug_id}: expected detectors did not fail: {sorted(missing)}"
