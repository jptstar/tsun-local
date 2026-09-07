from pathlib import Path

path = Path("tests/test_tsun_dump_tool.py")
text = path.read_text(encoding="utf-8")
old_version = 'self.assertEqual(TOOL.TOOL_VERSION, "2.7.3")'
old_limit = "self.assertEqual(TOOL.MAX_LOGGER_WEB_PATHS, 10)"
if old_version not in text:
    raise SystemExit("2.7.3 version expectation not found")
if old_limit not in text:
    raise SystemExit("10-page limit expectation not found")
text = text.replace(old_version, 'self.assertEqual(TOOL.TOOL_VERSION, "2.7.4")', 1)
text = text.replace(old_limit, "self.assertEqual(TOOL.MAX_LOGGER_WEB_PATHS, 24)", 1)
path.write_text(text, encoding="utf-8")
