# Інтеграційні тести Р-22

**Фікстури** (`app/tests/lab06/conftest.py`). `database_url` має `scope="session"`: контейнер `postgres:18-alpine` (версію образу зафіксовано) запускається один раз на весь запуск тестів, бо старт контейнера триває кілька секунд, і для кожного тесту це було б надто повільно. `repository` має рівень функції: кожен тест працює в транзакції `connection.transaction(force_rollback=True)`, яку відкочено навіть після успішного тесту. Тести не бачать даних один одного і можуть використовувати однакові `id`. Без відкату тест «повторний id» залежав би від того, чи запускався раніше тест, що вже додав студента з `id=1`.

Без Docker фікстура пропускає тести з причиною «Docker недоступний» (локально), а в CI ранер `ubuntu-latest` має Docker, тож усі тести виконуються в завданні `tests`.

| Пункт Р-22 | Тест | Результат | Issue | Чи знайшов би тест на фейку бази даних |
|------------|------|-----------|-------|----------------------------------------|
| `create_schema` створює таблиці, якщо їх немає | `test_create_schema_is_idempotent` | passed | — | Ні: у фейку немає схеми |
| `add` зберігає студента з оцінками, email, формою навчання і статусом; `get` повертає рівного | `test_added_student_is_returned_equal`, `test_student_without_grades_and_email` | passed | — | Частково: перетворення типів (enum → TEXT → enum, DATE) перевіряє лише справжня база |
| Повторний `id` → `DuplicateStudentError` | `test_add_duplicate_id_raises` | xfailed | [#37](https://github.com/lerabo/testing-course-bondarchuk/issues/37) | Так, якщо фейк перевіряв би дублікати — але повідомив би про інший виняток |
| Після дубля вміст не змінюється, репозиторієм можна користуватися | `test_duplicate_keeps_data_and_repository_usable` | xfailed | [#37](https://github.com/lerabo/testing-course-bondarchuk/issues/37) | **Ні**: «транзакцію перервано» (`InFailedSqlTransaction`) — поведінка саме PostgreSQL |
| `get` впорядковує оцінки за датою | `test_grades_are_returned_ordered_by_date` | passed | — | Ні: порядок задає `ORDER BY` у SQL |
| `get` неіснуючого → `StudentNotFoundError` | `test_get_missing_student_raises` | passed | — | Так |
| `add_grade` додає оцінку; для неіснуючого студента → `StudentNotFoundError`, репозиторій придатний далі | `test_add_grade_appends_grade`, `test_add_grade_to_missing_student_raises_and_repository_stays_usable` | passed | — | Ні: помилку визначає зовнішній ключ і вкладена транзакція |
| `find`: регістр, кирилиця | `test_find[lowercase]`, `test_find[uppercase]` | xfailed | [#38](https://github.com/lerabo/testing-course-bondarchuk/issues/38) | Залежить від фейку: фейк з `casefold()` дав би правильний результат і приховав би дефект SQL |
| `find`: пробіли на початку і в кінці | `test_find[surrounding-spaces]` | passed | — | Так |
| `find`: `%` і `_` буквально | `test_find[percent]`, `test_find[underscore]` | xfailed | [#39](https://github.com/lerabo/testing-course-bondarchuk/issues/39) | **Ні**: шаблони — це семантика `LIKE` |
| `find`: порожній запит → усі; середина прізвища; одна літера; немає збігів | `test_empty_query_returns_everybody`, `test_find[middle-of-name]`, `[one-letter]`, `[no-match]`, `[exact-case]` | passed | — | Так |
| Однакові прізвища — за ім'ям | `test_same_last_names_ordered_by_first_name` | passed | — | Так |
| Порядок за українською абеткою (Ґ, Є, І, Ї) | `test_find_orders_by_ukrainian_alphabet` | xfailed | [#40](https://github.com/lerabo/testing-course-bondarchuk/issues/40) | **Ні**: порядок залежить від правила сортування бази даних і образу контейнера |
| Зворотне перетворення для довільних студентів | `test_student_survives_round_trip` (Hypothesis, `test_repository_properties.py`) | passed | — | Ні: обмеження TEXT і INTEGER є лише в PostgreSQL |

**Чому порядок залежить від образу.** `ORDER BY last_name` використовує правило сортування (collation) бази даних. У `postgres:18-alpine` база створена з `en_US.utf8` від libc, але musl в Alpine не має правил порівняння для локалей, тож рядки фактично порівнюються за кодами Unicode: Є, І, Ї (U+0404–U+0407) стоять перед А (U+0410), Ґ (U+0490) — після Я, а малі літери — після всіх великих. В образі на Debian (glibc) порядок був би іншим, тож тест на одному образі може пройти, а на іншому — ні. Надійне рішення — задати порядок явно в SQL (ICU-collation `uk-UA-x-icu`).

## Властивість на справжній базі

`test_student_survives_round_trip` генерує студентів через `st.builds(Student, ...)` з оцінками, упорядкованими за датою, і для кожного прикладу відкочує власну транзакцію (`force_rollback=True`). Через це перевірку `HealthCheck.function_scoped_fixture` вимкнено свідомо, а `deadline=None` — бо запити до бази інколи тривають довше за 200 мс.

Зі стратегією без обмежень Hypothesis знайшов дві різні відмови і звузив їх до:

```text
psycopg.errors.NumericValueOutOfRange: integer out of range
    student=Student(id=2_147_483_648, first_name='', last_name='', grades=[], ...)
psycopg.DataError: PostgreSQL text fields cannot contain NUL (0x00) bytes
    student=Student(id=0, first_name='', last_name='\x00', grades=[], ...)
```

**Рішення.** Обидві ситуації — обмеження бази даних, яких специфікація Р-22 не описує: стовпець `id INTEGER` не вміщує значень понад 2³¹ − 1, а тип TEXT у PostgreSQL не може містити символ NUL. Справжні id студентів і імена таких значень не мають, тож це прогалина у вимогах, а не дефект коду. У стратегії `id` обмежено діапазоном 1…2³¹ − 1, а з тексту виключено `\x00` (і сурогатні символи, які не кодуються в UTF-8), з коментарем у тесті. Для замовника: варто доповнити Р-22 обмеженнями на id і текстові поля або перевіряти їх у `add` зі зрозумілою помилкою. Також звужений приклад показав, що репозиторій приймає порожні ім'я і прізвище (`''`) — специфікація цього теж не забороняє.
