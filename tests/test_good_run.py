"""Every check must PASS on the correct ETL."""
import pytest

from dataguard.checks import CHECKS, Ctx
from dataguard.pipeline import build


@pytest.mark.parametrize("chk", CHECKS, ids=[c.id for c in CHECKS])
def test_check_passes_on_good_run(chk):
    ok, detail = chk.fn(Ctx(build(upto=chk.stage), ()))
    assert ok, f"{chk.title} -> {detail}"
