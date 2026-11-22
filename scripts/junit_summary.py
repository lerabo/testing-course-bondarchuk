"""Підсумок звітів JUnit XML у Markdown для сторінки запуску GitHub Actions.

Використання: python junit_summary.py reports/junit-*.xml >> "$GITHUB_STEP_SUMMARY"
pytest записує xfail як skipped з типом pytest.xfail; тут їх рахують окремо,
щоб відомі дефекти не губилися серед пропущених тестів.
"""

import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def outcome(case: ET.Element) -> tuple[str, str]:
    """Результат тесту і перший рядок повідомлення про відмову.

    pytest-playwright з трасуванням додає перед failure елемент properties,
    тому шукаємо потрібний елемент, а не беремо перший дочірній.
    """
    for child in case:
        if child.tag in ("failure", "error"):
            return child.tag, child.get("message", "").strip().partition("\n")[0]
        if child.tag == "skipped":
            kind = "xfail" if child.get("type") == "pytest.xfail" else "skipped"
            return kind, ""
    return "passed", ""


def main(paths: list[str]) -> None:
    print("| Набір | Пройшло | Впало | Помилки | xfail | Пропущено | Час, с |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    failed = []
    for path in map(Path, paths):
        suite = ET.parse(path).getroot().find("testsuite")
        counts: Counter[str] = Counter()
        for case in suite.iter("testcase"):
            result, message = outcome(case)
            counts[result] += 1
            if result in ("failure", "error"):
                failed.append(
                    f"`{case.get('classname')}.{case.get('name')}`: {message}"
                )
        print(
            f"| {path.stem} | {counts['passed']} | {counts['failure']}"
            f" | {counts['error']} | {counts['xfail']} | {counts['skipped']}"
            f" | {float(suite.get('time', 0)):.1f} |"
        )
    if failed:
        print("\n**Відмови:**\n")
        print("\n".join(f"- {line}" for line in failed))


if __name__ == "__main__":
    main(sys.argv[1:])
