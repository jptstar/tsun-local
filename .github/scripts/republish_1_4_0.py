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

source = gzip.decompress(base64.b64decode(payload))
exec(compile(source, __file__, "exec"))

# This generator is intentionally one-shot. The resulting stable commit keeps
# only the real source, documentation and tests, not the republish payload.
for part in PARTS:
    part.unlink()
PAYLOAD_DIR.rmdir()
Path(__file__).unlink()
