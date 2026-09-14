from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once("tools/tsun_dump.py", 'TOOL_VERSION = "2.8.4"', 'TOOL_VERSION = "2.8.5"')
replace_once(
    "tools/tsun_dump.py",
    '''            "capture_status": "tuya_oem_candidate",
            "detected_protocol": "tuya-lan",
            "protocol_validation_status": "experimental_oem_transport",
            "model_family": "Tuya / ThingClips OEM candidate",
            "model_supplied_by_user": args.model,
            "pv_count": None,
''',
    '''            "capture_status": (
                "partial_success" if confirmed else "transport_unconfirmed"
            ),
            "detected_protocol": "tuya-lan",
            "protocol_validation_status": (
                "transport_detected" if confirmed else "transport_unconfirmed"
            ),
            "capture_limitation": "encrypted_status_requires_local_key",
            "measurements_available": False,
            "device_reachable": confirmed,
            "requires_local_key_for_status": True,
            "model_family": "Tuya / ThingClips OEM candidate",
            "model_supplied_by_user": args.model,
            "pv_count": None,
''',
)
replace_once(
    "tools/tsun_dump.py",
    '''        "tuya_lan": {
            "candidate_confirmed": confirmed,
            "tcp_6668": tcp,
''',
    '''        "tuya_lan": {
            "candidate_confirmed": confirmed,
            "transport_detected": confirmed,
            "tcp_6668": tcp,
''',
)
replace_once(
    "tools/tsun_dump.py",
    '''            "status_read_attempted": False,
            "status_read_reason": (
                "Tuya LAN status is encrypted and requires the device-specific "
                "local key; the diagnostic does not request or store that secret."
            ),
            "device_id_requested": False,
            "local_key_requested": False,
            "configuration_write_performed": False,
''',
    '''            "status_read_attempted": False,
            "status_read_blocked_by": "missing_local_key",
            "status_read_reason": (
                "Tuya LAN status is encrypted and requires the device-specific "
                "local key; the diagnostic does not request or store that secret."
            ),
            "device_id_requested": False,
            "local_key_requested": False,
            "local_key_stored": False,
            "configuration_write_performed": False,
''',
)
replace_once(
    "tools/tsun_dump.py",
    '''    print(f"Protocol : {document['metadata']['detected_protocol']}")
    print(
''',
    '''    print(f"Protocol : {document['metadata']['detected_protocol']}")
    capture_status = document["metadata"].get("capture_status")
    if capture_status:
        print(f"Status   : {capture_status}")
    if document["metadata"].get("detected_protocol") == "tuya-lan":
        print("Measures : unavailable (encrypted status requires local key)")
    print(
''',
)

helper = '''
_MODEL_POWER_RE = re.compile(
    r"^TSOL-(?:MS|MX|MP|MG|ML)(?P<power>\\d{3,4})(?:D(?:-T)?|Elite|Lite)?$",
    re.IGNORECASE,
)


def _model_nominal_power(model: str) -> int | None:
    match = _MODEL_POWER_RE.fullmatch(model.strip())
    return int(match.group("power")) if match else None


def _diagnostic_rated_power(diagnostic: dict[str, Any]) -> int | None:
    measurements = diagnostic.get("decoded_known_measurements")
    if not isinstance(measurements, dict):
        return None
    for key in ("rated_power", "max_designed_power"):
        value = measurements.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        rounded = int(round(float(value)))
        if 1 <= rounded <= 20000:
            return rounded
    return None


def _expanded_declared_models(
    declared_devices: Iterable[dict[str, Any]],
) -> list[str]:
    result: list[str] = []
    for index, item in enumerate(declared_devices):
        if not isinstance(item, dict):
            raise ReportUploadError(f"declared device {index + 1} is invalid")
        model = _assert_string(str(item.get("model", "")), "device model", 80)
        if not model:
            raise ReportUploadError("device model cannot be empty")
        try:
            quantity = int(item.get("quantity", 1))
        except (TypeError, ValueError) as exc:
            raise ReportUploadError("device quantity must be an integer") from exc
        if not 1 <= quantity <= 99:
            raise ReportUploadError("device quantity must be between 1 and 99")
        result.extend([model] * quantity)
        if len(result) > 99:
            raise ReportUploadError("too many declared inverter units")
    return result


def _pop_model(remaining: list[str], model: str) -> bool:
    wanted = model.casefold()
    for index, candidate in enumerate(remaining):
        if candidate.casefold() == wanted:
            remaining.pop(index)
            return True
    return False


def _annotate_model(
    diagnostic: dict[str, Any], model: str, method: str
) -> None:
    metadata = diagnostic.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        raise ReportUploadError("diagnostic metadata must contain an object")
    metadata["model_supplied_by_user"] = model
    metadata["model_assignment"] = {
        "source": "declared_inventory",
        "method": method,
        "confidence": "unambiguous",
    }


def associate_declared_models(
    diagnostics: list[dict[str, Any]],
    declared_devices: Iterable[dict[str, Any]],
) -> dict[int, str]:
    """Assign declared models to individual dumps only when unambiguous."""
    remaining = _expanded_declared_models(declared_devices)
    if not diagnostics or len(remaining) != len(diagnostics):
        return {}

    unresolved: set[int] = set(range(len(diagnostics)))
    for index, diagnostic in enumerate(diagnostics):
        metadata = diagnostic.get("metadata")
        existing = (
            metadata.get("model_supplied_by_user")
            if isinstance(metadata, dict)
            else None
        )
        if isinstance(existing, str) and existing.strip():
            if not _pop_model(remaining, existing.strip()):
                return {}
            unresolved.discard(index)

    assignments: dict[int, str] = {}
    progress = True
    while progress:
        progress = False
        for index in sorted(tuple(unresolved)):
            rated = _diagnostic_rated_power(diagnostics[index])
            if rated is None:
                continue
            candidates: dict[str, str] = {}
            for model in remaining:
                if _model_nominal_power(model) == rated:
                    candidates.setdefault(model.casefold(), model)
            if len(candidates) != 1:
                continue
            model = next(iter(candidates.values()))
            _annotate_model(diagnostics[index], model, "rated_power_match")
            _pop_model(remaining, model)
            unresolved.remove(index)
            assignments[index] = model
            progress = True

    if unresolved and len(remaining) == len(unresolved):
        distinct = {model.casefold(): model for model in remaining}
        if len(distinct) == 1:
            model = next(iter(distinct.values()))
            for index in sorted(unresolved):
                _annotate_model(
                    diagnostics[index], model, "remaining_declared_inventory"
                )
                assignments[index] = model
            remaining.clear()
            unresolved.clear()

    return assignments


def annotate_report_files(
    paths: Iterable[Path],
    declared_devices: Iterable[dict[str, Any]],
) -> dict[Path, str]:
    """Persist safe per-report model links before upload when resolvable."""
    path_list = [Path(path) for path in paths]
    device_list = list(declared_devices)
    if not path_list or not device_list:
        return {}
    diagnostics = [load_diagnostic(path) for path in path_list]
    assignments = associate_declared_models(diagnostics, device_list)
    result: dict[Path, str] = {}
    for index, model in assignments.items():
        path = path_list[index]
        diagnostic = validate_diagnostic(diagnostics[index])
        encoded = (
            json.dumps(diagnostic, ensure_ascii=False, indent=2) + "\\n"
        ).encode("utf-8")
        if len(encoded) > MAX_REPORT_BYTES:
            raise ReportUploadError(
                f"diagnostic file is too large after model annotation: {path.name}"
            )
        temporary = path.with_suffix(path.suffix + ".model.tmp")
        try:
            temporary.write_bytes(encoded)
            temporary.replace(path)
        except OSError as exc:
            raise ReportUploadError(
                f"cannot annotate diagnostic file: {path.name}"
            ) from exc
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        result[path] = model
    return result
'''
replace_once(
    "tools/tsun_report_upload.py",
    "\n\ndef build_payload(\n",
    "\n\n" + helper.strip("\n") + "\n\ndef build_payload(\n",
)

replace_once(
    "tools/tsun_diagnostic_app.py",
    '''    def _upload_reports(self, paths: list[Path], tester_name: str, devices: list[dict[str, Any]]) -> None:
        for current, path in enumerate(paths, 1):
''',
    '''    def _upload_reports(self, paths: list[Path], tester_name: str, devices: list[dict[str, Any]]) -> None:
        try:
            report_upload.annotate_report_files(paths, devices)
        except report_upload.ReportUploadError as exc:
            self.upload_events.put(("error", str(exc)))
            return
        for current, path in enumerate(paths, 1):
''',
)

replace_once("tools/tsun_diagnostic.py", 'APP_VERSION = "1.5.12"', 'APP_VERSION = "1.5.13"')

p = Path("tests/test_tsun_dump_tuya.py")
text = p.read_text(encoding="utf-8")
old_imports = "import sys\nimport unittest\n"
new_imports = "import sys\nfrom types import SimpleNamespace\nfrom unittest import mock\nimport unittest\n"
if text.count(old_imports) != 1:
    raise SystemExit("tests/test_tsun_dump_tuya.py: import marker mismatch")
text = text.replace(old_imports, new_imports, 1)
marker = '''    def test_tuya_capture_contract_excludes_secrets_and_writes(self) -> None:
'''
test = '''    def test_confirmed_tuya_capture_is_partial_success_not_failure(self) -> None:
        args = SimpleNamespace(
            tcp_scan_timeout=0.2,
            full=True,
            model="TSOL-MS800",
            protocol="auto",
            interval=3.0,
        )
        discovery = {
            "tuya_udp_seen": False,
            "tuya_framing": [],
            "tuya_udp_ports": [],
        }
        with mock.patch.object(
            TOOL,
            "_tuya_tcp_reachability",
            return_value={
                "reachable": True,
                "connect_latency_ms": 12.0,
                "application_payload_sent": False,
            },
        ):
            document = TOOL.capture_tuya_candidate(args, "192.0.2.10", discovery)

        metadata = document["metadata"]
        self.assertEqual(metadata["capture_status"], "partial_success")
        self.assertEqual(metadata["protocol_validation_status"], "transport_detected")
        self.assertFalse(metadata["measurements_available"])
        self.assertTrue(metadata["requires_local_key_for_status"])
        self.assertEqual(metadata["model_supplied_by_user"], "TSOL-MS800")
        self.assertEqual(document["tuya_lan"]["status_read_blocked_by"], "missing_local_key")
        self.assertFalse(document["tuya_lan"]["local_key_requested"])
        self.assertFalse(document["tuya_lan"]["local_key_stored"])
        self.assertFalse(document["tuya_lan"]["application_payload_sent"])

'''
if text.count(marker) != 1:
    raise SystemExit("tests/test_tsun_dump_tuya.py: insertion marker mismatch")
p.write_text(text.replace(marker, test + marker, 1), encoding="utf-8")

p = Path("tests/test_diagnostic_report_upload.py")
text = p.read_text(encoding="utf-8")
marker = '''    def test_upload_success_returns_report_receipt(self) -> None:
'''
tests = '''    def test_associates_unambiguous_inventory_and_tuya_leftover(self) -> None:
        diagnostics = [
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 450}},
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 300}},
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 450}},
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {}},
        ]
        devices = [
            {"model": "TSOL-MX450", "quantity": 2},
            {"model": "TSOL-MS800", "quantity": 1},
            {"model": "TSOL-MS300", "quantity": 1},
        ]
        assigned = upload.associate_declared_models(diagnostics, devices)
        self.assertEqual(
            assigned,
            {
                0: "TSOL-MX450",
                1: "TSOL-MS300",
                2: "TSOL-MX450",
                3: "TSOL-MS800",
            },
        )
        self.assertEqual(
            diagnostics[3]["metadata"]["model_assignment"]["method"],
            "remaining_declared_inventory",
        )

    def test_same_power_families_remain_unassigned_when_ambiguous(self) -> None:
        diagnostics = [
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 800}},
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 800}},
        ]
        devices = [
            {"model": "TSOL-MS800", "quantity": 1},
            {"model": "TSOL-MX800", "quantity": 1},
        ]
        self.assertEqual(upload.associate_declared_models(diagnostics, devices), {})
        self.assertIsNone(diagnostics[0]["metadata"]["model_supplied_by_user"])
        self.assertIsNone(diagnostics[1]["metadata"]["model_supplied_by_user"])

    def test_inventory_count_mismatch_does_not_guess(self) -> None:
        diagnostics = [
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 450}},
        ]
        devices = [{"model": "TSOL-MX450", "quantity": 2}]
        self.assertEqual(upload.associate_declared_models(diagnostics, devices), {})
        self.assertIsNone(diagnostics[0]["metadata"]["model_supplied_by_user"])

    def test_annotation_is_persisted_before_upload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tuya.json"
            path.write_text(
                json.dumps(
                    {
                        "metadata": {"model_supplied_by_user": None},
                        "decoded_known_measurements": {},
                    }
                ),
                encoding="utf-8",
            )
            assigned = upload.annotate_report_files(
                [path], [{"model": "TSOL-MS800", "quantity": 1}]
            )
            self.assertEqual(assigned, {path: "TSOL-MS800"})
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["metadata"]["model_supplied_by_user"], "TSOL-MS800")
            self.assertEqual(
                saved["metadata"]["model_assignment"]["confidence"], "unambiguous"
            )

'''
if text.count(marker) != 1:
    raise SystemExit("tests/test_diagnostic_report_upload.py: insertion marker mismatch")
p.write_text(text.replace(marker, tests + marker, 1), encoding="utf-8")
