"""Тести для непокритих розгалужень, знайдених аналізом покриття (ЛР 5, завдання 5)."""

import json

import pytest

from student_portal.exceptions import (
    ImportFormatError,
    InvalidGradeError,
    StorageError,
    StudentNotFoundError,
)
from student_portal.grades import Grade, ects_grade
from student_portal.group import Group
from student_portal.importer import import_students
from student_portal.people import Funding, Student
from student_portal.status import Status
from student_portal.storage import load_group, save_group

HEADER = "last_name;first_name;email;funding\n"


def known_defect(issue: str):
    return pytest.mark.xfail(strict=True, reason=f"відомий дефект {issue}")


def make_group() -> Group:
    group = Group("КН-11")
    group.add(Student(1, "Олена", "Коваль", [Grade("Python", 95)], "o@uni.edu"))
    group.add(Student(2, "Андрій", "Мельник", [Grade("Python", 45)], "a@uni.edu"))
    return group


# ---------------------------------------------------------------- Р-05


@pytest.mark.parametrize(
    ("points", "letter"),
    [
        (100, "A"),
        (90, "A"),
        (89, "B"),
        (82, "B"),
        (81, "C"),
        (75, "C"),
        (74, "D"),
        (67, "D"),
        (66, "E"),
        (60, "E"),
        (59, "Fx"),
        (0, "Fx"),
    ],
)
def test_ects_grade_boundaries(points, letter):
    assert ects_grade(points) == letter


@pytest.mark.parametrize("points", [-1, 101])
def test_ects_grade_out_of_range_rejected(points):
    with pytest.raises(InvalidGradeError):
        ects_grade(points)


# ---------------------------------------------------------------- storage


def test_save_and_load_round_trip(tmp_path):
    # Arrange
    group = make_group()
    group.get(2).funding = Funding.CONTRACT
    group.get(2).status = Status.ON_LEAVE
    path = tmp_path / "nested" / "group.json"
    # Act
    save_group(group, path)
    loaded = load_group(path)
    # Assert
    assert [s.full_name for s in loaded] == ["Коваль Олена", "Мельник Андрій"]
    assert loaded.get(2).funding == Funding.CONTRACT
    assert loaded.get(2).status == Status.ON_LEAVE
    assert loaded.get(1).grades == group.get(1).grades


def test_load_missing_file(tmp_path):
    with pytest.raises(StorageError, match="не знайдено"):
        load_group(tmp_path / "absent.json")


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("{not json", id="invalid-json"),
        pytest.param(json.dumps({"students": []}), id="missing-name"),
        pytest.param(
            json.dumps({"name": "КН-11", "students": [{"id": 1}]}),
            id="missing-fields",
        ),
    ],
)
def test_load_malformed_file(tmp_path, content):
    path = tmp_path / "group.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(StorageError, match="неправильний формат"):
        load_group(path)


# ---------------------------------------------------------------- group


def test_remove_student():
    group = make_group()
    removed = group.remove(1)
    assert removed.last_name == "Коваль"
    with pytest.raises(StudentNotFoundError):
        group.get(1)


def test_group_statistics():
    group = make_group()
    group.add(Student(3, "Ірина", "Шевчук"))
    assert group.average() == 70
    assert group.courses() == {"Python"}
    assert group.ects_distribution() == {"A": 1, "Fx": 1}


def test_group_without_grades_has_no_average():
    assert Group("КН-12").average() is None


# ---------------------------------------------------------------- Р-19


def write_csv(tmp_path, rows: str, *, bom: bool = False):
    path = tmp_path / "import.csv"
    path.write_text(("﻿" if bom else "") + HEADER + rows, encoding="utf-8")
    return path


def test_import_missing_file(tmp_path):
    with pytest.raises(StorageError):
        import_students(make_group(), tmp_path / "absent.csv")


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        pytest.param(";Тарас;t@uni.edu;бюджет\n", "обов’язкові", id="empty-last-name"),
        pytest.param("Гнатюк;Тарас;t@uni.edu;грант\n", "фінансування", id="funding"),
        pytest.param("Петренко;Іван;o@uni.edu;\n", "уже є в групі", id="duplicate"),
    ],
)
def test_import_invalid_row_rejected(tmp_path, rows, message):
    with pytest.raises(ImportFormatError, match=message):
        import_students(make_group(), write_csv(tmp_path, rows))


@known_defect("#8")
def test_import_accepts_bom(tmp_path):
    path = write_csv(tmp_path, "Гнатюк;Тарас;t@uni.edu;бюджет\n", bom=True)
    assert import_students(make_group(), path) == 1


@known_defect("#7")
def test_import_is_atomic(tmp_path):
    group = make_group()
    path = write_csv(tmp_path, "Гнатюк;Тарас;t@uni.edu;бюджет\nСидор;;s@uni.edu;\n")
    with pytest.raises(ImportFormatError):
        import_students(group, path)
    assert len(group.students) == 2


@known_defect("#9")
def test_import_duplicate_email_ignores_case(tmp_path):
    path = write_csv(tmp_path, "Петренко;Іван;O@UNI.EDU;бюджет\n")
    with pytest.raises(ImportFormatError):
        import_students(make_group(), path)


@known_defect("#12")
def test_import_strips_names(tmp_path):
    group = make_group()
    import_students(group, write_csv(tmp_path, "  Гнатюк ; Тарас ;t@uni.edu;\n"))
    assert group.get(3).full_name == "Гнатюк Тарас"
