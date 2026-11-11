# Мутаційний аналіз

**Налаштування.** `[tool.mutmut]` у `app/pyproject.toml`: мутуються `corrections.py` (Р-08), `scholarship.py` (Р-17) і `retake.py` (Р-21). Тести — `tests/lab05` і `tests/lab06/test_mutants.py`, без інтеграційних (кожен мутант запускав би контейнер). mutmut використовує `fork`, тож аналіз виконувався в GitHub Actions на Linux (тимчасова гілка з окремим workflow, у `main` не злита): мутаційний аналіз не входить у конвеєр запитів на злиття, бо він дорогий.

**Підсумок:** базова лінія — вбито 34 з 36 (94,4 %), після роботи — вбито 36 з 36 (100 %), еквівалентних — 0.

```text
$ uv run mutmut results --all true
student_portal.retake.x_is_working_day__mutmut_1..3: killed
student_portal.retake.x_retake_date__mutmut_1..14: killed
student_portal.scholarship.x_scholarship__mutmut_1..6: killed
student_portal.corrections.x_correct_grade__mutmut_1..13: killed   (базова лінія: 7 і 9 - survived)
```

Мутанти `retake.py` убиті всі вже в базовій лінії — це наслідок TDD у ЛР 5: кожен рядок з'являвся лише для того, щоб пройшов тест.

## Живі мутанти

| Мутант | Зміна | Чому вижив | Рішення |
|--------|-------|------------|---------|
| `corrections.x_correct_grade__mutmut_7` | `deadline = grade.graded_on + timedelta(days=CORRECTION_DAYS)` → `graded_on - timedelta(...)` | Тести ЛР 3 перевіряють лише тип винятку `CorrectionPeriodError`, а дата в повідомленні не перевіряється | Тест `test_period_error_message_names_last_correction_day`: для оцінки від 01.10.2026 повідомлення містить «до 15.10.2026 включно» (Р-08, приклад консолі з ЛР 3) |
| `corrections.x_correct_grade__mutmut_9` | текст повідомлення → `None` | Те саме: повідомлення не перевірялось | Той самий тест (`match=` падає на повідомленні `None`) |

Код застосунку не змінювався, `# pragma: no mutate` не знадобився.

## Мутант умови `elapsed >= CORRECTION_DAYS` (завдання 2.5)

Мутант `corrections.x_correct_grade__mutmut_5` замінює `>=` на `>`. Це саме те виправлення, якого потребує дефект [#14](https://github.com/lerabo/testing-course-bondarchuk/issues/14) (14-й день строку відхиляється). Його вбив тест `test_correction_accepted[TB-BVA-07]`, позначений `xfail(strict=True)`: з мутантом тест несподівано проходить (`XPASS`), а `strict=True` перетворює `XPASS` на помилку, тож mutmut бачить червоний запуск. Інші тести мутанта не помічають: для d = 15 і d = 20 обидві умови однаково відхиляють виправлення.

Якби тест TB-BVA-07 мав `xfail` без `strict=True`, `XPASS` вважався б успіхом, мутант вижив би, а mutmut показав би живого мутанта, який насправді виправляє дефект. Тобто `strict=True` робить тест на відомий дефект корисним і для мутаційного аналізу: він сигналізує про будь-яку зміну поведінки на межі.
