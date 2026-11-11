"""Властивість зворотного перетворення для Р-22 на справжній базі даних."""

from datetime import date

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.status import Status

# PostgreSQL TEXT не зберігає байт NUL, а стовпець id має тип INTEGER: ці
# обмеження бази даних специфікація Р-22 не описує, тому стратегія їх враховує
# (рішення - у docs/lab06/03-integration.md).
text = st.text(
    st.characters(blacklist_characters="\x00", blacklist_categories=("Cs",)),
    min_size=1,
    max_size=30,
)
grades = st.lists(
    st.builds(
        Grade,
        course=text,
        score=st.integers(0, 100),
        graded_on=st.dates(date(2000, 1, 1), date(2030, 12, 31)),
    ),
    max_size=5,
).map(lambda items: sorted(items, key=lambda g: g.graded_on))
students = st.builds(
    Student,
    id=st.integers(1, 2**31 - 1),
    first_name=text,
    last_name=text,
    grades=grades,
    email=st.none() | st.emails(),
    funding=st.sampled_from(Funding),
    status=st.sampled_from(Status),
)

# Кожен приклад відкочує власну транзакцію, тому спільна фікстура безпечна.
per_example = settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)


@per_example
@given(student=students)
def test_student_survives_round_trip(repository, student):
    with repository.connection.transaction(force_rollback=True):
        repository.add(student)
        assert repository.get(student.id) == student
