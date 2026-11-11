# Відповідність тестів ЛР 3

Тести лежать у `app/tests/lab05/test_lab03_cases.py`. Кожна техніка — один параметризований тест (для Р-08 — три, за типом очікуваного результату); ідентифікатори наборів даних збігаються з таблицями `docs/lab03/`. Кожен тест має структуру Arrange-Act-Assert, а тести недопустимих переходів перевіряють і виняток, і незмінність статусу та оцінок.

Відомі дефекти позначено `xfail(strict=True)` з номером issue з ЛР 4: тест очікувано падає і не робить CI червоним, а коли дефект виправлять, `XPASS` стане помилкою — тоді мітку треба зняти, а issue закрити. Кількість `xfailed` (8) дорівнює кількості відмов у ЛР 3.

```text
$ uv run pytest tests/lab05/test_lab03_cases.py -rxX -q
46 passed, 8 xfailed
```

| Тестовий випадок ЛР 3 | Тест pytest | Результат | Issue |
|---|---|---|---|
| TB-BVA-01 | `test_correction_invalid_score_rejected[TB-BVA-01]` | passed | — |
| TB-BVA-02 | `test_correction_accepted[TB-BVA-02]` | passed | — |
| TB-BVA-03 | `test_correction_accepted[TB-BVA-03]` | passed | — |
| TB-BVA-04 | `test_correction_invalid_score_rejected[TB-BVA-04]` | passed | — |
| TB-BVA-05 | `test_correction_accepted[TB-BVA-05]` | passed | — |
| TB-BVA-06 | `test_correction_accepted[TB-BVA-06]` | passed | — |
| TB-BVA-07 | `test_correction_accepted[TB-BVA-07]` | xfailed | #14 |
| TB-BVA-08 | `test_correction_outside_period_rejected[TB-BVA-08]` | passed | — |
| TB-DT-01 | `test_scholarship_decision_table[TB-DT-01]` | passed | — |
| TB-DT-02 | `test_scholarship_decision_table[TB-DT-02]` | passed | — |
| TB-DT-03 | `test_scholarship_decision_table[TB-DT-03]` | passed | — |
| TB-DT-04 | `test_scholarship_decision_table[TB-DT-04]` | passed | — |
| TB-DT-05 | `test_scholarship_decision_table[TB-DT-05]` | passed | — |
| TB-DT-06 | `test_scholarship_decision_table[TB-DT-06]` | passed | — |
| TB-DT-07 | `test_scholarship_decision_table[TB-DT-07]` | xfailed | #15 |
| TB-DT-08 | `test_scholarship_decision_table[TB-DT-08]` | passed | — |
| TB-DT-09 | `test_scholarship_decision_table[TB-DT-09]` | passed | — |
| TB-DT-10 | `test_scholarship_decision_table[TB-DT-10]` | passed | — |
| TB-DT-11 | `test_scholarship_decision_table[TB-DT-11]` | passed | — |
| TB-DT-12 | `test_scholarship_decision_table[TB-DT-12]` | passed | — |
| TB-DT-13 | `test_scholarship_decision_table[TB-DT-13]` | passed | — |
| TB-DT-14 | `test_scholarship_decision_table[TB-DT-14]` | passed | — |
| TB-DT-15 | `test_scholarship_decision_table[TB-DT-15]` | passed | — |
| TB-DT-16 | `test_scholarship_decision_table[TB-DT-16]` | passed | — |
| TB-DT-17 | `test_scholarship_decision_table[TB-DT-17]` | passed | — |
| TB-DT-18 | `test_scholarship_decision_table[TB-DT-18]` | passed | — |
| TB-EP-01 | `test_correction_accepted[TB-EP-01]` | passed | — |
| TB-EP-02 | `test_correction_outside_period_rejected[TB-EP-02]` | xfailed | #18 |
| TB-EP-03 | `test_correction_outside_period_rejected[TB-EP-03]` | passed | — |
| TB-EP-04 | `test_correction_invalid_score_rejected[TB-EP-04]` | passed | — |
| TB-EP-05 | `test_correction_invalid_score_rejected[TB-EP-05]` | passed | — |
| TB-EP-06 | `test_correction_invalid_score_rejected[TB-EP-06]` | xfailed | #19 |
| TB-EP-07 | `test_correction_invalid_score_rejected[TB-EP-07]` | xfailed | #19 |
| TB-EP-08 | `test_correction_outside_period_rejected[TB-EP-08]` | passed | — |
| TB-ST-01 | `test_valid_transition_sequence[TB-ST-01]` | passed | — |
| TB-ST-02 | `test_valid_transition_sequence[TB-ST-02]` | passed | — |
| TB-ST-03 | `test_graduate_with_fx_rejected` | passed | — |
| TB-ST-04 | `test_invalid_transition_rejected[TB-ST-04]` | passed | — |
| TB-ST-05 | `test_invalid_transition_rejected[TB-ST-05]` | passed | — |
| TB-ST-06 | `test_invalid_transition_rejected[TB-ST-06]` | passed | — |
| TB-ST-07 | `test_invalid_transition_rejected[TB-ST-07]` | passed | — |
| TB-ST-08 | `test_invalid_transition_rejected[TB-ST-08]` | passed | — |
| TB-ST-09 | `test_invalid_transition_rejected[TB-ST-09]` | xfailed | #17 |
| TB-ST-10 | `test_invalid_transition_rejected[TB-ST-10]` | passed | — |
| TB-ST-11 | `test_invalid_transition_rejected[TB-ST-11]` | passed | — |
| TB-ST-12 | `test_invalid_transition_rejected[TB-ST-12]` | passed | — |
| TB-ST-13 | `test_invalid_transition_rejected[TB-ST-13]` | passed | — |
| TB-ST-14 | `test_invalid_transition_rejected[TB-ST-14]` | passed | — |
| TB-ST-15 | `test_invalid_transition_rejected[TB-ST-15]` | passed | — |
| TB-ST-16 | `test_invalid_transition_rejected[TB-ST-16]` | passed | — |
| TB-ST-17 | `test_invalid_transition_rejected[TB-ST-17]` | xfailed | #16 |
| TB-ST-18 | `test_invalid_transition_rejected[TB-ST-18]` | passed | — |
| TB-ST-19 | `test_invalid_transition_rejected[TB-ST-19]` | passed | — |
| TB-ST-20 | `test_invalid_transition_rejected[TB-ST-20]` | xfailed | #17 |

Окремо в `test_coverage_gaps.py` позначено xfail чотири дефекти імпорту з ЛР 4 (#7, #8, #9, #12): ці тести з'явилися під час аналізу покриття (див. `04-coverage.md`).
