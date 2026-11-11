# Тести REST API (Р-23)

Тести — `app/tests/lab07/`. Фікстура `base_url` (`conftest.py`) запускає API у фоновому потоці на вільному порту з копією `data/group.json`; сервер спільний для всіх тестів, тому кожен тест, що змінює дані, створює власного студента з унікальним email (`new_student`, `created`), а дані з `group.json` лише читає. Відповіді перевіряються схемами `STUDENT_SCHEMA` і `GRADE_SCHEMA` з `additionalProperties: false` (`api_schemas.py`): зайве поле у відповіді (наприклад, хеш пароля) зробило б тест червоним.

| Запит Р-23 | Що перевірено (класи, межі, ролі) | Тести | Результат |
|------------|-----------------------------------|-------|-----------|
| `GET /api/students` | Схема кожного елемента; середній бал Коваль Олени 92,5; фільтр `group` (КН-11 → лише ця група, невідома група → `[]`) | `test_students_api.py::test_list_matches_schema_and_data`, `test_group_filter_keeps_only_that_group`, `test_unknown_group_gives_empty_list` | пройдено |
| `POST /api/students` | 201, `Location: /api/students/{id}`, тіло за схемою, `average: null`, кругова перевірка через `Location`; невідомі поля ігноруються | `test_create_returns_location_and_reads_back`, `test_unknown_fields_are_ignored` | пройдено |
| `POST /api/students` — поля тіла | Довжина `first_name` і `last_name`: 0 → 422, 1 → 201, 50 → 201, 51 → 422; неправильний email, `null` у кожному полі, відсутнє кожне поле → 422 (кожен недопустимий клас окремим тестом) | `test_name_length[*]` (8), `test_invalid_value_rejected[*]` (4), `test_missing_field_rejected[*]` (3) | пройдено |
| `POST /api/students` — унікальність email | Email Коваль у верхньому регістрі → 409 | `test_create_with_existing_email_in_other_case_conflicts` | пройдено |
| `GET /api/students/{id}` | Схема, дані з `group.json`; неіснуючий → 404 | `test_get_student_matches_schema`, `test_get_missing_student_is_404` | пройдено |
| `PUT /api/students/{id}` | Зміну видно наступним `GET`; власний email можна зберегти; порожнє ім'я → 422; неіснуючий → 404; email іншого студента в іншому регістрі → 409 | `test_update_is_visible_in_next_get`, `test_update_keeps_own_email`, `test_update_with_invalid_body_rejected`, `test_update_missing_student_is_404`, `test_update_to_other_students_email_conflicts` | дефект [#47](https://github.com/lerabo/testing-course-bondarchuk/issues/47) (унікальність під час зміни), решта пройдено |
| `DELETE /api/students/{id}` | 204 без тіла, після цього `GET` → 404; неіснуючий → 404 | `test_delete_then_get_is_404`, `test_delete_missing_student_is_404` | дефект [#48](https://github.com/lerabo/testing-course-bondarchuk/issues/48) (неіснуючий → 204) |
| `POST /api/grades` | Межі `score` за Р-04: −1 → 422, 0, 1, 100 → 201, 101 → 422; межі літер ECTS за Р-05 (59/60, 66/67, 74/75, 81/82, 89/90); дробове, `null`, порожня дисципліна, дисципліна 101 символ → 422, 100 символів → 201; неіснуючий студент → 404 | `test_grades_api.py::test_valid_score_gives_ects_letter[*]` (13), `test_invalid_grade_rejected[*]` (6), `test_course_of_100_chars_accepted`, `test_grade_for_missing_student_is_404` | дефект [#46](https://github.com/lerabo/testing-course-bondarchuk/issues/46) (0 балів → 422), решта пройдено |
| `GET /api/students/{id}/grades` і побічні дії | Після двох оцінок (80 і 91) середній 85,5, список з літерами C і A в порядку виставлення | `test_two_grades_update_average_and_list` | пройдено |

Правило «оцінку не можна виставити за правилами застосунку (студента відраховано) → 409» через API не перевірено: API не має запиту для зміни статусу, тож відрахованого студента не можна створити без зміни даних сервера.

## Контроль доступу

Таблиця в `test_access.py` (`EXPECTED`): ролі — без токена, невідомий токен, адміністратор, викладач, студент 1; запити — усі сім запитів Р-23. Запити до конкретного студента виконуються до студента `{new}`, створеного в тесті, тому навіть зламаний контроль доступу (наприклад, `DELETE` викладачем) не зачепить інших тестів. Для студента 1 цей студент — чужий об'єкт, тож рядок студента перевіряє BOLA/IDOR.

| Роль \ запит | GET список | POST студент | GET {new} | PUT {new} | DELETE {new} | POST оцінка | GET {new}/grades |
|---|---|---|---|---|---|---|---|
| без токена | 401 | 401 | 401 | 401 | 401 | 401 | 401 |
| невідомий токен | 401 | 401 | 401 | 401 | 401 | 401 | 401 |
| адміністратор | 200 | 201 | 200 | 200 | 204 | 403 | 200 |
| викладач | 200 | 403 | 200 | **403 → 200, #44** | 403 | 201 | 200 |
| студент 1 (чужий об'єкт) | 403 | 403 | 403 | 403 | 403 | 403 | **403 → 200, #45** |

Окремо (`test_own_data_and_check_order`): студент 1 бачить власну картку й оцінки (200), студент 2 — свою картку і не бачить картки студента 1 (403); порядок перевірок — студент 1 отримує 403 і для неіснуючого id (картка — так, оцінки — 404, дефект #45), викладач і адміністратор для неіснуючого — 404, без токена — 401.

Знайдено два класи порушень з OWASP API Security Top 10: доступ до функції, недоступної ролі (API5:2023, викладач змінює студента, [#44](https://github.com/lerabo/testing-course-bondarchuk/issues/44)), і доступ до чужого об'єкта (API1:2023 BOLA, студент читає чужі оцінки, [#45](https://github.com/lerabo/testing-course-bondarchuk/issues/45)).
