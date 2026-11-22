import pytest
import gameplay.damage_pipeline as mod

CASES = [
    ("resistance_multiply", (0.5, 0.5)),
    ("armor_segment", (100.0, 200.0)),
    ("crit_order", (1.5, 1.2)),
    ("dot_snapshot", (10.0, 1.5)),
    ("shield_after", (100.0, 40.0)),
    ("damage_floor", (5.0, 0.0)),
    ("final_round", (3.7,)),
    ("server_authority", (1, 2)),
    ("ledger_record", (1, 2)),
    ("localized_number", (12345.0, 3)),
    ("immunity_check", (0.9, 0.2)),
    ("pierce_calc", (20.0, 0.3)),
    ("heal_convert", (-5.0, 0.0)),
    ("overflow_track", (150.0, 100.0)),
    ("element_split", ([0.3, 0.7],)),
]

@pytest.mark.parametrize("fn_name,args", CASES)
def test_contract(fn_name, args):
    fn = getattr(mod, fn_name)
    assert fn(*args) is not None
