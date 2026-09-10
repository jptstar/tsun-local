from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


path = Path("tools/tsun_dump.py")
text = path.read_text(encoding="utf-8")

text = replace_once(
    text,
    "import urllib.request\n",
    "import urllib.error\nimport urllib.request\n",
    "urllib.error import",
)
text = replace_once(
    text,
    'TOOL_VERSION = "2.7.4"',
    'TOOL_VERSION = "2.7.5"',
    "tool version",
)
text = replace_once(
    text,
    'REPORT_EMAIL = "dev@jptstar.com"\n',
    '''REPORT_EMAIL = "dev@jptstar.com"\nREPORT_UPLOAD_URL = "https://tsun-local-reports-uploader.jp-810.workers.dev/report"\nREPORT_UPLOAD_MAX_BYTES = 524288\nREPORT_UPLOAD_TIMEOUT = 20.0\nREPORT_UPLOAD_FORBIDDEN_KEYS = frozenset(\n    {\n        "monitor_sn",\n        "monitor_serial",\n        "serial_number",\n        "logger_ip",\n        "ip_address",\n        "mac",\n        "mac_address",\n        "ssid",\n        "password",\n        "wifi_password",\n        "token",\n        "access_token",\n        "refresh_token",\n        "email",\n        "e_mail",\n    }\n)\n''',
    "upload constants",
)

upload_helpers = r'''

class ReportUploadError(RuntimeError):
    """Raised when a generated diagnostic cannot be safely submitted."""


def _find_forbidden_upload_key(
    value: Any, path: str = "$", depth: int = 0
) -> str | None:
    """Return the first forbidden privacy field in a diagnostic tree."""
    if depth > 40:
        raise ReportUploadError("diagnostic nesting is too deep")
    if isinstance(value, list):
        for index, child in enumerate(value):
            found = _find_forbidden_upload_key(
                child, f"{path}[{index}]", depth + 1
            )
            if found is not None:
                return found
        return None
    if not isinstance(value, dict):
        return None
    for key, child in value.items():
        key_text = str(key)
        if key_text.lower() in REPORT_UPLOAD_FORBIDDEN_KEYS:
            return f"{path}.{key_text}"
        found = _find_forbidden_upload_key(child, f"{path}.{key_text}", depth + 1)
        if found is not None:
            return found
    return None


def validate_diagnostic_for_upload(diagnostic: Any) -> dict[str, Any]:
    """Apply the local privacy gate before any report transmission."""
    if not isinstance(diagnostic, dict):
        raise ReportUploadError("diagnostic JSON must contain an object")
    forbidden = _find_forbidden_upload_key(diagnostic)
    if forbidden is not None:
        raise ReportUploadError(
            f"diagnostic contains a forbidden privacy field: {forbidden}"
        )
    return diagnostic


def load_diagnostic_for_upload(path: Path) -> dict[str, Any]:
    """Load and privacy-check one generated diagnostic from disk."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ReportUploadError(f"cannot read diagnostic file: {path.name}") from exc
    if size <= 0:
        raise ReportUploadError(f"diagnostic file is empty: {path.name}")
    if size > REPORT_UPLOAD_MAX_BYTES:
        raise ReportUploadError(f"diagnostic file is too large: {path.name}")
    try:
        diagnostic = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReportUploadError(
            f"diagnostic file is not valid JSON: {path.name}"
        ) from exc
    return validate_diagnostic_for_upload(diagnostic)


def _upload_server_error_message(exc: urllib.error.HTTPError) -> str:
    """Return a bounded server error without exposing response internals."""
    try:
        raw = exc.read(4096)
        body = json.loads(raw.decode("utf-8", errors="replace"))
        message = body.get("error") if isinstance(body, dict) else None
    except (OSError, ValueError, UnicodeError):
        message = None
    if isinstance(message, str) and message.strip():
        return message.strip()
    return f"HTTP {exc.code}"


def upload_diagnostic_report(
    diagnostic: dict[str, Any],
    *,
    consent: bool,
    endpoint: str = REPORT_UPLOAD_URL,
    timeout: float = REPORT_UPLOAD_TIMEOUT,
) -> dict[str, Any]:
    """Submit one anonymized diagnostic after explicit user consent."""
    if consent is not True:
        raise ReportUploadError("explicit consent is required")
    diagnostic = validate_diagnostic_for_upload(diagnostic)
    payload = {
        "schema_version": 1,
        "consent": True,
        "tester_profile": {"name": "", "declared_devices": []},
        "diagnostic": diagnostic,
    }
    body = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    if len(body) > REPORT_UPLOAD_MAX_BYTES:
        raise ReportUploadError("report is too large after adding upload metadata")

    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"TSUN-Local-Diagnostic-Python/{TOOL_VERSION}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read(REPORT_UPLOAD_MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise ReportUploadError(
            f"upload rejected: {_upload_server_error_message(exc)}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        raise ReportUploadError("upload service is unreachable") from exc

    if len(response_body) > REPORT_UPLOAD_MAX_BYTES:
        raise ReportUploadError("upload service returned an invalid response")
    try:
        result = json.loads(response_body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReportUploadError("upload service returned invalid JSON") from exc
    if not isinstance(result, dict) or result.get("ok") is not True:
        message = result.get("error") if isinstance(result, dict) else None
        raise ReportUploadError(str(message or "upload failed"))
    if not isinstance(result.get("report_id"), str):
        raise ReportUploadError("upload service did not return a report ID")
    return result


def _submit_completed_reports(paths: list[Path]) -> None:
    """Validate every report first, then transmit them one by one."""
    validated = [(path, load_diagnostic_for_upload(path)) for path in paths]
    print("\nSending anonymized report(s) securely to TSUN Local...")
    for path, diagnostic in validated:
        result = upload_diagnostic_report(diagnostic, consent=True)
        report_id = result["report_id"]
        print(f"  {path.name}: sent successfully · report ID {report_id}")
        view_url = result.get("view_url")
        if isinstance(view_url, str) and view_url.strip():
            print(f"    Secure report link: {view_url.strip()}")


def _print_email_report_instructions(paths: list[Path]) -> None:
    """Show the same manual email fallback offered by the desktop app."""
    print("\nManual email fallback")
    print(f"Email: {REPORT_EMAIL}")
    print("Attach the generated JSON file(s):")
    for path in paths:
        print(f"  {path}")
    print("No report was transmitted automatically.")


def _handle_report_delivery(paths: list[Path], args: argparse.Namespace) -> int:
    """Offer secure upload, email fallback or local-only retention."""
    if args.submit:
        choice = "1"
    elif args.no_submit:
        print("No report was transmitted. Generated JSON remains local.")
        return 0
    elif sys.stdin is None or not sys.stdin.isatty():
        print("No report was transmitted because this is a non-interactive session.")
        print("Use --submit for explicit secure upload, or send the JSON manually to " + REPORT_EMAIL + ".")
        return 0
    else:
        print("\n=== Share diagnostic report ===")
        print("1) Send securely to TSUN Local (I consent to transmit the anonymized JSON)")
        print("2) Send manually by email")
        print("3) Keep the report locally / do not send")
        try:
            choice = input("Choice [1/2/3]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNo report was transmitted.")
            return 0

    if choice == "1":
        try:
            _submit_completed_reports(paths)
        except ReportUploadError as exc:
            print(f"Secure upload failed: {exc}", file=sys.stderr)
            _print_email_report_instructions(paths)
            return 1 if args.submit else 0
        return 0
    if choice == "2":
        _print_email_report_instructions(paths)
        return 0

    print("No report was transmitted. Generated JSON remains local.")
    return 0
'''

text = replace_once(
    text,
    "\n\n# ---------------------------------------------------------------------------\n# CLI\n# ---------------------------------------------------------------------------\n",
    upload_helpers
    + "\n\n# ---------------------------------------------------------------------------\n# CLI\n# ---------------------------------------------------------------------------\n",
    "upload helper insertion",
)

text = replace_once(
    text,
    '''    parser.add_argument(\n        "--check-update",\n        action="store_true",\n        help="check diagnostic-latest for a newer tsun_dump.py and exit",\n    )\n    return parser\n''',
    '''    parser.add_argument(\n        "--check-update",\n        action="store_true",\n        help="check diagnostic-latest for a newer tsun_dump.py and exit",\n    )\n    delivery = parser.add_mutually_exclusive_group()\n    delivery.add_argument(\n        "--submit",\n        "--upload",\n        dest="submit",\n        action="store_true",\n        help=(\n            "explicitly consent to upload generated anonymized JSON report(s) "\n            "through the TSUN Local secure report service"\n        ),\n    )\n    delivery.add_argument(\n        "--no-submit",\n        action="store_true",\n        help="keep generated report(s) local and skip the end-of-run sharing prompt",\n    )\n    return parser\n''',
    "CLI submit options",
)

text = replace_once(
    text,
    '''    print("TSUN Local Hardware Validation Dump Tool")\n    print(f"Standalone v{TOOL_VERSION} · READ-ONLY · Python standard library only")\n    print(f"Send generated JSON reports to: {REPORT_EMAIL}")\n    print("No inverter configuration write operation is implemented.\\n")\n''',
    '''    print("TSUN Local Hardware Validation Dump Tool")\n    print(f"Standalone v{TOOL_VERSION} · READ-ONLY · Python standard library only")\n    print("At the end, choose secure upload, email fallback, or keep the report local.")\n    print("No inverter configuration write operation is implemented.\\n")\n''',
    "startup wording",
)

text = replace_once(
    text,
    '''    if completed:\n        print("Generated files:")\n        for output in completed:\n            print(f"  {output}")\n        print(f"Send the generated JSON file(s) to: {REPORT_EMAIL}")\n        return 0\n    return 1\n''',
    '''    if completed:\n        print("Generated files:")\n        for output in completed:\n            print(f"  {output}")\n        delivery_result = _handle_report_delivery(completed, args)\n        if failed:\n            return 1\n        return delivery_result\n    return 1\n''',
    "end-of-run delivery",
)

path.write_text(text, encoding="utf-8")

# The graphical desktop application already owns its consent/upload workflow.
# Prevent the embedded CLI engine from displaying a second sharing prompt.
gui_path = Path("tools/tsun_diagnostic_gui.py")
gui = gui_path.read_text(encoding="utf-8")
gui = replace_once(
    gui,
    '        args = ["tsun_dump.py", "--full"]\n',
    '        args = ["tsun_dump.py", "--full", "--no-submit"]\n',
    "desktop no-submit bridge",
)
gui_path.write_text(gui, encoding="utf-8")

# Keep the existing standalone contract current.
test_path = Path("tests/test_tsun_dump_tool.py")
test = test_path.read_text(encoding="utf-8")
test = replace_once(
    test,
    'self.assertEqual(TOOL.TOOL_VERSION, "2.7.4")',
    'self.assertEqual(TOOL.TOOL_VERSION, "2.7.5")',
    "standalone tool version test",
)
test_path.write_text(test, encoding="utf-8")

# Document the new terminal workflow without changing the desktop flow.
docs_path = Path("docs/HARDWARE_DUMP.md")
docs = docs_path.read_text(encoding="utf-8")
anchor = "python3 tsun_dump.py --full\n```"
replacement = '''python3 tsun_dump.py --full\n```\n\nAt the end of an interactive run, the Python tool now asks whether to:\n\n1. securely submit the anonymized JSON to TSUN Local,\n2. keep it for manual email to `dev@jptstar.com`, or\n3. keep it locally without transmitting anything.\n\nNothing is uploaded without an explicit choice. For scripted use, `--submit` (alias `--upload`) is explicit consent to upload, while `--no-submit` disables the prompt and keeps the report local.''' 
if anchor not in docs:
    raise SystemExit("hardware dump docs: command anchor not found")
docs = docs.replace(anchor, replacement, 1)
docs_path.write_text(docs, encoding="utf-8")
