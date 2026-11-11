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
| P-08 | — | — | US-1: «Teacher corrects a grade within 72 hours…», «Teacher cannot change a grade after 72 hours» | — |
| P-09 | РП-04 | ЯВ-08 | — (юзабіліті-тест) | — |
| P-10 | РП-09, РП-10 | ЯВ-05 | — (моніторинг) | — |
| P-11 | РП-08 | ЯВ-07 | — | — |
| P-12 | РП-02 | ЯВ-02 | US-3: «Student cannot view another student's grades» | — |
| P-13 | РП-05 | ЯВ-03 | US-1: «Teacher corrects a grade within 72 hours and the change is logged» | — |
| P-14 | РП-07 | ЯВ-06 | — (навантажувальний тест) | — |
| P-15 | — | — | US-2: «Non-university email is rejected» | — |
| P-16 | РП-09 | ЯВ-04 | US-3: «Account is locked after three failed login attempts» | — |

**Перевірка покриття.** Усі ризики високого рівня (РП-01…РП-04) мають сценарій приймання або вимогу до якості з методом перевірки. Без сценарію приймання лишаються P-03, P-09, P-10, P-11, P-14 — це нефункціональні вимоги, їх перевіряють ЯВ-05…ЯВ-08 (навантажувальні, юзабіліті-тести, моніторинг). P-11 варто покрити сценарієм у наступній історії користувача про відомість.
