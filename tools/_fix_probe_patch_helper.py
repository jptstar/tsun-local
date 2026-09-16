#!/usr/bin/env python3
from pathlib import Path
import re

path = Path(__file__).with_name("_apply_probe_catalog_patch.py")
text = path.read_text(encoding="utf-8")
pattern = re.compile(
    r'\nsource = replace_once\(\n'
    r'    source,\n'
    r'    \'\'\'    raw_observations = .*?'
    r'    "failure fallback invocation",\n'
    r'\)\n',
    re.DOTALL,
)
replacement = r'''
source = replace_once(
    source,
    '''    try:\n        logger_web = capture_logger_web_pages(host, args.http_page_timeout)\n''',
    '''    research_detection = run_research_probe_catalog(\n        host,\n        args.port,\n        sn,\n        args.timeout,\n        requested=args.protocol,\n        hint=discovery.get("protocol_hint"),\n        full=full,\n    )\n    try:\n        logger_web = capture_logger_web_pages(host, args.http_page_timeout)\n''',
    "failure fallback invocation",
)
'''
text, count = pattern.subn("\n" + replacement, text, count=1)
if count != 1:
    raise RuntimeError(f"could not harden failure fallback anchor: {count}")
path.write_text(text, encoding="utf-8")
print("Hardened probe-catalog patch helper")
'''
