"""Схеми відповідей за Р-23 і генератор даних нового студента (ЛР 7)."""

import itertools

_counter = itertools.count(1)

STUDENT_SCHEMA = {
    "type": "object",
    "required": ["id", "first_name", "last_name", "email", "group", "average"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "first_name": {"type": "string", "minLength": 1, "maxLength": 50},
        "last_name": {"type": "string", "minLength": 1, "maxLength": 50},
        "email": {"type": "string", "format": "email"},
        "group": {"type": "string"},
        "average": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
    },
    "additionalProperties": False,
}

GRADE_SCHEMA = {
    "type": "object",
    "required": ["course", "score", "ects", "graded_on"],
    "properties": {
        "course": {"type": "string", "minLength": 1, "maxLength": 100},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "ects": {"enum": ["A", "B", "C", "D", "E", "Fx"]},
        "graded_on": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
    },
    "additionalProperties": False,
}


def unique_student() -> dict[str, str]:
    n = next(_counter)
    return {
        "first_name": "Тарас",
        "last_name": "Гнатюк",
        "email": f"t.hnatiuk{n}@students.example.edu",
    }
