# Оновлення залежностей

У ЛР 10 pip-audit знайшов у `python-multipart==0.0.22` шість вразливостей ([#85](https://github.com/lerabo/testing-course-bondarchuk/issues/85)). Оновлення - окремий запит [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) з гілки `deps/update`; команди виконано в GitHub Actions (uv 0.13.9, Python 3.14), бо з робочого середовища немає доступу до PyPI.

```text
uv tree --outdated --depth 1                 # застарілі прямі залежності: 10 з 19
uv add "python-multipart>=0.0.31"            # зняти точне закріплення ==0.0.22; uv обрав 0.0.34
uvx pip-audit -r requirements.txt --no-deps --disable-pip          → No known vulnerabilities found
uv lock --upgrade                            # решта в межах pyproject.toml: 31 оновлення, 1 видалення
uvx pip-audit … (сервіс PyPI і -s osv)       → No known vulnerabilities found
uv run pytest -W error::DeprecationWarning -m "not e2e"
  340 passed, 74 deselected, 57 xfailed; 34 snapshots passed
```

`uv add` змінює вимогу в `pyproject.toml` і оновлює в lock-файлі лише цей пакет із залежностями; `uv lock --upgrade-package <пакет>` оновлює в lock-файлі один пакет у межах наявних вимог, не змінюючи `pyproject.toml`; `uv lock --upgrade` - усі пакети в межах вимог. Тому для вразливої залежності потрібен `uv add`: точне `==0.0.22` не дозволило б `uv lock --upgrade` її підняти, і саме тому Dependabot її не запропонував. `-W error::DeprecationWarning` перетворює попередження про застарілий API на помилку: те, що зараз лише попередження, у наступній MAJOR-версії буде видалено, і краще дізнатися про це зараз. Попереджень немає. Регресійний набір - тести ЛР 5–11 і конвеєр ЛР 9 (зокрема інтеграційні з PostgreSQL і e2e): `ci-ok` зелений. Навіть PATCH-оновлення перевіряють так само: семантичне версіонування - обіцянка автора, а не гарантія, а для версій 0.x будь-яка MINOR може ламати сумісність.

| Пакет | Група | Було | Стало | SemVer | Що перевірено | Запит на злиття |
|---|---|---|---|---|---|---|
| python-multipart | продакшн, пряма | 0.0.22 | 0.0.34 | PATCH (0.0.x - може ламати) | pip-audit (PyPI, OSV): вразливостей немає; журнал змін: 0.0.26–0.0.31 - виправлення шести вразливостей ЛР 10, 0.0.33 - обмеження полів urlencoded, прибрано Python 3.10 (у нас ≥ 3.12); тести Р-27 імпорту і ЛР 10 зелені | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| annotated-doc | продакшн | 0.0.5 | 0.0.7 | PATCH (0.0.x - може ламати) | PATCH (залежність fastapi); тести API | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| certifi | продакшн | 2026.10.23 | 2026.11.20 | CalVer | оновлення сертифікатів (CalVer) | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| charset-normalizer | dev | 3.5.2 | 3.5.3 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| click | продакшн | 8.5.0 | 8.5.1 | PATCH | PATCH (залежність uvicorn); запуск сервера в e2e | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| coverage | dev | 7.17.0 | 7.17.5 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| email-validator | продакшн | 2.3.0 | 2.4.0 | MINOR | транзитивна (pydantic[email]); тести валідації email ЛР 7 і імпорту ЛР 10 | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| fastapi | продакшн, пряма | 0.162.0 | 0.165.0 | MINOR (0.x - може ламати) | журнал змін 0.163–0.165: нові налаштовувані обмеження розміру тіла запиту і розбору форм, змін, що ламають, немає; контрактні тести ЛР 7, тести API і безпеки ЛР 10 | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| graphql-core | dev | 3.3.1 | 3.3.2 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| harfile | dev | 0.6.0 | 0.7.1 | MINOR (0.x - може ламати) | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| httpcore2 | dev | 2.16.0 | 2.16.2 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| httpx2 | dev, пряма | 2.16.0 | 2.16.2 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| hypothesis | dev, пряма | 6.170.12 | 6.170.17 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| hypothesis-graphql | dev | 0.13.6 | 0.13.7 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| jsonschema-rs | dev | 0.60.3 | 0.63.1 | MINOR (0.x - може ламати) | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| markdown-it-py | dev | 4.2.0 | 4.3.0 | MINOR | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| mdit-py-plugins | dev | 0.6.1 | 0.7.0 | MINOR (0.x - може ламати) | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| mutmut | dev, пряма | 3.8.0 | 3.8.1 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| pact-python-ffi | dev | 0.5.12.1 | 0.5.13.0 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| platformdirs | dev | 4.13.6 | 4.14.8 | MINOR | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| playwright | dev | 1.64.1 | 1.65.2 | MINOR | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| psycopg | продакшн, пряма | 3.3.6 | 3.3.9 | PATCH | PATCH; інтеграційні тести ЛР 6 з PostgreSQL (Testcontainers) у конвеєрі | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| psycopg-binary | продакшн | 3.3.6 | 3.3.9 | PATCH | PATCH, разом із psycopg | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| pydantic | продакшн, пряма | 2.14.3 | 2.14.4 | PATCH | PATCH; тести API і схем ЛР 7 | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| pydantic-core | продакшн | 2.50.4 | 2.50.5 | PATCH | PATCH, разом із pydantic | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| pytest | dev, пряма | 9.1.1 | 9.2.0 | MINOR | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| python-slugify | dev | 9.1.3 | 9.2.0 | MINOR | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| pyyaml | dev | 6.0.3 | 6.0.4 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| ruff | dev, пряма | 0.17.1 | 0.17.6 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| schemathesis | dev, пряма | 4.33.1 | 4.34.0 | MINOR | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| tzdata | продакшн | 2026.5 | 2026.6 | CalVer | оновлення бази часових поясів (CalVer) | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| wrapt | dev | 2.5.1 | 2.5.2 | PATCH | регресійний набір (-W error::DeprecationWarning) і конвеєр | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |
| pyee | dev (залежність playwright) | 14.0.0 | - | видалено | playwright 1.65 більше не потребує; e2e у конвеєрі | [#95](https://github.com/lerabo/testing-course-bondarchuk/pull/95) |

MAJOR-оновлень немає. Dependabot з ЛР 9 відкрив [#73](https://github.com/lerabo/testing-course-bondarchuk/pull/73) (fastapi 0.162.0 → 0.165.0) і [#72](https://github.com/lerabo/testing-course-bondarchuk/pull/72) (група dev-tools: httpx2, hypothesis, mutmut, pytest, ruff - ті самі версії, schemathesis 4.33.4 проти 4.34.0 у #95). Мій запит покриває обидва і, на відміну від них, оновлює `python-multipart` - Dependabot з `lockfile-only` не змінює точне закріплення в `pyproject.toml`. #72 і #73 застаріли; Dependabot закриває такі запити сам, коли бачить оновлену залежність у `main`.
