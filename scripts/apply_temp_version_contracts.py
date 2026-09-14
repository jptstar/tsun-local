from pathlib import Path


def replace_all_checked(path: str, old: str, new: str, expected: int) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} matches for {old!r}, found {count}")
    p.write_text(text.replace(old, new), encoding="utf-8")


replace_all_checked(
    "tests/test_diagnostic_desktop_test_mode.py",
    '"1.5.12"',
    '"1.5.13"',
    3,
)
replace_all_checked(
    "tests/test_diagnostic_upload_gui.py",
    '"1.5.12"',
    '"1.5.13"',
    1,
)
replace_all_checked(
    "tests/test_tsun_dump_tool.py",
    '"2.8.4"',
    '"2.8.5"',
    1,
)
