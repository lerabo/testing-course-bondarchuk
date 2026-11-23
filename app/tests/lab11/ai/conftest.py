"""Рішення щодо тестів ШІ (docs/lab11/02-ai-tests.md): відхилені - skip з причиною.

Файли тестів ШІ лишаються такими, як їх згенерувала модель; позначки ставляться тут.
"""

import pytest

PINS_DEFECT = "відхилено: закріплює дефект"
REJECTED = {
    # набір «за кодом»
    (
        "test_full_transcript_exact_output",
        None,
    ): f"{PINS_DEFECT} #92, #93 (FX, 74 - «добре»)",
    ("test_grade_scales_boundaries", 74): f"{PINS_DEFECT} #93 (74 - «добре»)",
    ("test_grade_scales_boundaries", 59): f"{PINS_DEFECT} #92 (FX замість Fx)",
    ("test_grade_scales_boundaries", 35): f"{PINS_DEFECT} #92 (FX замість Fx)",
    ("test_grade_scales_boundaries", 34): f"{PINS_DEFECT} #92 (F замість Fx)",
    ("test_grade_scales_boundaries", 0): f"{PINS_DEFECT} #92 (F замість Fx)",
    ("test_latest_grade_by_date_wins_regardless_of_list_order", None): (
        f"{PINS_DEFECT} #92: перевіряє літеру FX"
    ),
    ("test_credits_table_constant", None): (
        "відхилено: прив'язаний до реалізації - перевіряє внутрішню константу"
    ),
    ("test_separator_width_is_w_and_appears_twice", None): (
        "відхилено: прив'язаний до реалізації - перевіряє константу W"
    ),
}


def pytest_collection_modifyitems(items):
    for item in items:
        params = getattr(item, "callspec", None)
        score = params.params.get("score") if params else None
        reason = REJECTED.get((item.originalname, score))
        if reason:
            item.add_marker(pytest.mark.skip(reason=reason))
