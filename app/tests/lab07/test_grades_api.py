"""Р-23: виставлення оцінок POST /api/grades (Р-04, Р-05) і GET .../grades."""

import pytest
from api_schemas import GRADE_SCHEMA
from jsonschema import validate


def grade_for(location: str, **overrides):
    student_id = int(location.rsplit("/", 1)[1])
    return {"student_id": student_id, "course": "Python", "score": 80} | overrides


@pytest.mark.parametrize(
    ("score", "letter"),
    [
        (0, "Fx"),
        (1, "Fx"),
        (59, "Fx"),
        (60, "E"),
        (66, "E"),
        (67, "D"),
        (74, "D"),
        (75, "C"),
        (81, "C"),
        (82, "B"),
        (89, "B"),
        (90, "A"),
        (100, "A"),
    ],
)
def test_valid_score_gives_ects_letter(teacher, created, score, letter):
    location, _ = created
    response = teacher.post("/api/grades", json=grade_for(location, score=score))
    assert response.status_code == 201
    validate(response.json(), GRADE_SCHEMA)
    assert (response.json()["score"], response.json()["ects"]) == (score, letter)


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"score": -1}, id="score--1"),
        pytest.param({"score": 101}, id="score-101"),
        pytest.param({"score": 75.5}, id="score-fraction"),
        pytest.param({"score": None}, id="score-null"),
        pytest.param({"course": ""}, id="course-empty"),
        pytest.param({"course": "К" * 101}, id="course-101"),
    ],
)
def test_invalid_grade_rejected(teacher, created, overrides):
    location, _ = created
    response = teacher.post("/api/grades", json=grade_for(location, **overrides))
    assert response.status_code == 422


def test_course_of_100_chars_accepted(teacher, created):
    location, _ = created
    response = teacher.post("/api/grades", json=grade_for(location, course="К" * 100))
    assert response.status_code == 201


def test_grade_for_missing_student_is_404(teacher):
    body = {"student_id": 99999, "course": "Python", "score": 80}
    assert teacher.post("/api/grades", json=body).status_code == 404


def test_two_grades_update_average_and_list(teacher, admin, created):
    location, _ = created
    teacher.post("/api/grades", json=grade_for(location, course="Python", score=80))
    teacher.post("/api/grades", json=grade_for(location, course="Мережі", score=91))
    assert admin.get(location).json()["average"] == 85.5
    response = admin.get(f"{location}/grades")
    assert response.status_code == 200
    grades = response.json()
    for grade in grades:
        validate(grade, GRADE_SCHEMA)
    assert [(g["course"], g["ects"]) for g in grades] == [
        ("Python", "C"),
        ("Мережі", "A"),
    ]
