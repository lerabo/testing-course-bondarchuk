# Тестові дублери для Р-20

Тести — `app/tests/lab05/test_reminders_doubles.py`. Справжні листи не надсилаються. Дату розсилки передано параметром `today=date(2026, 1, 15)`, тож очікуваний термін (14.02.2026) не залежить від поточного дня.

| Тест | Залежність | Вид дублера | Що перевіряє: стан чи поведінку | Чому саме цей вид |
|------|------------|-------------|---------------------------------|-------------------|
| `test_debtor_gets_letter_with_subject_courses_and_deadline` | `Mailer` | Фейк (`FakeMailer`) | Стан: вміст `outbox` (адреса, тема, дисципліни лише з Fx, дата) і звіт | Читабельно, перевіряємо результат, а не спосіб виклику; не залежить від бібліотеки дублерів |
| `test_debtor_with_several_debts_gets_one_letter` (xfail #29) | `Mailer` | Фейк | Стан: у `outbox` один лист з «Бази даних, Python» | Кількість і вміст листів зручно перевіряти як список |
| `test_no_debtors_no_letters` | `Mailer` | Фейк | Стан: `outbox` порожній, звіт порожній | Те саме |
| `test_active_debtor_is_notified_once` | `Mailer` | Mock з `create_autospec(Mailer, instance=True)` | Поведінку: `assert_called_once`, `call_args` | Перевіряємо саму взаємодію з поштовиком |
| `test_reminder_not_sent[...]` (академвідпустка і випускник — xfail #30; відрахований, без email, без Fx) | `Mailer` | Mock з автоспецифікацією | Поведінку: `assert_not_called` | «Лист **не** надіслано» — це відсутність виклику, її природно перевіряє mock |
| `test_autospec_rejects_wrong_call_signature` | `Mailer` | Mock з автоспецифікацією | Поведінку дублера: виклик з неіснуючим аргументом дає `TypeError` | Показує, навіщо `create_autospec`: звичайний `Mock()` прийняв би будь-яку сигнатуру, і тест пройшов би з помилкою в коді |
| `test_failed_letter_does_not_stop_mailing` (xfail #31) | `Mailer` | Mock з автоспецифікацією і `side_effect = [ConnectionError(...), None]` | Поведінку (2 виклики) і стан звіту (`sent`, `failed`) | `side_effect` дає змогу зімітувати збій сервера на першому листі й успіх на другому |
| `test_smtp_mailer_connects_with_starttls_and_login` | клас `smtplib.SMTP` | Підміна через `mocker.patch("student_portal.reminders.SMTP", autospec=True)` | Поведінку: хост і порт 587, `starttls()` перед `login(...)`, заголовки From/To/Subject і текст листа | Справжній клас відкрив би мережеве з'єднання |
| `test_smtp_mailer_without_username_does_not_login` | клас `smtplib.SMTP` | Підміна через `mocker` | Поведінку: `starttls` і `send_message` викликано, `login` — ні | Те саме |

**Чому не `mocker.patch("smtplib.SMTP")`.** `reminders.py` робить `from smtplib import SMTP`: під час імпорту модуль копіює посилання на клас у власне ім'я `student_portal.reminders.SMTP`. Патч `smtplib.SMTP` замінює ім'я в модулі `smtplib`, але `SmtpMailer.send` бере клас зі свого модуля, тож тест намагався б з'єднатися зі справжнім сервером (і падав би на таймауті або DNS). Правило: підміняють ім'я в модулі, де його шукає код, що тестується, а не там, де його оголошено.

**Знайдені дефекти** (звіти за шаблоном ЛР 4, тести позначено `xfail(strict=True, reason="#N")`):

- [#29](https://github.com/lerabo/testing-course-bondarchuk/issues/29) — боржник з кількома Fx отримує окремий лист на кожну дисципліну, а не один;
- [#30](https://github.com/lerabo/testing-course-bondarchuk/issues/30) — нагадування надсилаються студентам в академвідпустці та випускникам;
- [#31](https://github.com/lerabo/testing-course-bondarchuk/issues/31) — збій надсилання одного листа зупиняє розсилку, список `failed` не заповнюється.

Кожен пункт специфікації Р-20 має щонайменше один тест: хто отримує (статус, email, Fx), один лист із темою, дисциплінами за абеткою і датою через 30 днів, продовження розсилки після збою, звіт `sent`/`failed`, а також `SmtpMailer` (з'єднання, STARTTLS, вхід за наявності імені).
