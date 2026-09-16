#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("_apply_probe_catalog_patch.py")
text = path.read_text(encoding="utf-8")

start_marker = "\nsource = replace_once(\n    source,\n    '''    raw_observations = (\\n"
end_marker = '    "failure fallback invocation",\n)\n'
start = text.find(start_marker)
if start < 0:
    raise RuntimeError("could not find failure fallback replacement block start")
end = text.find(end_marker, start)
if end < 0:
    raise RuntimeError("could not find failure fallback replacement block end")
end += len(end_marker)

replacement = r"""
source = replace_once(
    source,
    '''    try:\n        logger_web = capture_logger_web_pages(host, args.http_page_timeout)\n''',
    '''    research_detection = run_research_probe_catalog(\n        host,\n        args.port,\n        sn,\n        args.timeout,\n        requested=args.protocol,\n        hint=discovery.get("protocol_hint"),\n        full=full,\n    )\n    try:\n        logger_web = capture_logger_web_pages(host, args.http_page_timeout)\n''',
    "failure fallback invocation",
)
"""

text = text[:start] + "\n" + replacement + text[end:]
path.write_text(text, encoding="utf-8")
print("Hardened probe-catalog patch helper")
