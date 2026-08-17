#!/usr/bin/env python3
"""One-shot generator for the corrected TSUN Local 1.4.0 stable source."""

import base64
import gzip
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD_DIR = HERE / "republish_payload"
PARTS = sorted(PAYLOAD_DIR.iterdir())
payload = "".join(part.read_text(encoding="utf-8").strip() for part in PARTS)

expected = "e60c348dc0fe09b41c57367efbd8da4c482daeb1135ded51b50835b8b9b62ed7"
actual = hashlib.sha256(payload.encode()).hexdigest()
if actual != expected:
    raise SystemExit(f"Republish payload checksum mismatch: {actual}")

source_text = gzip.decompress(base64.b64decode(payload)).decode("utf-8")

# The original one-shot generator used a short expected-dict suffix that occurs
# in both the 02B0 and 1511 alarm tests. Target the 1511 class explicitly.
buggy = r'''    replace_once(
        "tests/test_protocols.py",
        '                "alarm_active": 1,\n            },\n',
        '                "alarm_active": 1,\n                "inverter_operating_state": "fault",\n            },\n',
    )
'''
fixed = r'''    path = ROOT / "tests/test_protocols.py"
    text = path.read_text(encoding="utf-8")
    class_marker = "class Protocol1511Tests(unittest.TestCase):"
    before, section = text.split(class_marker, 1)
    old = '                "alarm_active": 1,\n            },\n'
    new = '                "alarm_active": 1,\n                "inverter_operating_state": "fault",\n            },\n'
    if old not in section:
        raise RuntimeError("tests/test_protocols.py: 1511 alarm expectation not found")
    section = section.replace(old, new, 1)
    path.write_text(before + class_marker + section, encoding="utf-8")
'''
if buggy not in source_text:
    raise SystemExit("Republish source patch target not found")
source_text = source_text.replace(buggy, fixed, 1)
exec(compile(source_text, __file__, "exec"))

# This generator is intentionally one-shot. The resulting stable commit keeps
# only the real source, documentation and tests, not the republish payload.
for part in PARTS:
    part.unlink()
PAYLOAD_DIR.rmdir()
Path(__file__).unlink()
