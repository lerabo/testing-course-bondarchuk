# Матриця простежуваності

Матриця пов'язує вимоги (з виправленими формулюваннями з `01-requirements-review.md`), ризики, вимоги до якості та сценарії приймання. Колонку тестів буде доповнено на наступних лабораторних роботах.

| Вимога | Ризики | Вимоги до якості | Сценарії приймання | Тести |
|--------|--------|------------------|--------------------|-------|
| P-01 | — | — | US-2: «Administrator adds a student who can then log in», «Teacher cannot add a student» | — |
| P-02 | РП-06 | — | US-2: «Email that differs only in letter case is rejected as a duplicate» | — |
| P-03 | РП-07 | ЯВ-06 | — (перевіряється навантажувальним тестом) | — |
| P-04 | РП-03 | ЯВ-01 | US-1: «Score outside the allowed range or not an integer is rejected» | — |
| P-05 | РП-01 | ЯВ-01 | US-1: «ECTS grade is derived from the total score» | — |
| P-06 | — | — | US-3: «Student sees own grades with ECTS letters», «Anonymous user is redirected to the login page» | — |
| P-07 | РП-02 | ЯВ-02 | US-3: «Student cannot view another student's grades» | — |
| P-08 (уточнена в ЛР 3: 14 днів) | РП-11 | — | US-1: «Teacher corrects a grade within 14 days…», «Teacher cannot change a grade after 14 days» | ЛР 3: TB-EP-01…08, TB-BVA-01…08 |
| P-09 | РП-04 | ЯВ-08 | — (юзабіліті-тест) | — |
| P-10 | РП-09, РП-10 | ЯВ-05 | — (моніторинг) | — |
| P-11 | РП-08 | ЯВ-07 | — | — |
| P-12 | РП-02 | ЯВ-02 | US-3: «Student cannot view another student's grades» | — |
| P-13 | РП-05 | ЯВ-03 | US-1: «Teacher corrects a grade within 14 days and the change is logged» | — |
| P-14 | РП-07 | ЯВ-06 | — (навантажувальний тест) | — |
| P-15 | — | — | US-2: «Non-university email is rejected» | — |
| P-16 | РП-09 | ЯВ-04 | US-3: «Account is locked after three failed login attempts» | — |
| P-17 | РП-12 | ЯВ-01 | — | ЛР 3: TB-DT-01…18 |
| P-18 | РП-13 | — | — | ЛР 3: TB-ST-01…20 |

**ЛР 3.** Вимоги P-08 (уточнена), P-17 і P-18 та нові ризики РП-11…РП-13 покрито тестами чорної скриньки з `docs/lab03/`. Для P-17 і P-18 сценаріїв приймання ще немає — їх варто додати як нові історії користувача.

**Перевірка покриття.** Усі ризики високого рівня (РП-01…РП-04) мають сценарій приймання або вимогу до якості з методом перевірки. Без сценарію приймання лишаються P-03, P-09, P-10, P-11, P-14 — це нефункціональні вимоги, їх перевіряють ЯВ-05…ЯВ-08 (навантажувальні, юзабіліті-тести, моніторинг). P-11 варто покрити сценарієм у наступній історії користувача про відомість.
