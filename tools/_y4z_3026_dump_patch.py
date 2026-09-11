from pathlib import Path

path = Path("tools/tsun_dump.py")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one match, got {count}: {old[:120]!r}")
    text = text.replace(old, new, 1)


replace_once('TOOL_VERSION = "2.7.5"', 'TOOL_VERSION = "2.8.0"')

replace_once(
    "protocol families currently researched by TSUN Local: 1511, 02B0 and 1097.",
    "protocol families currently researched by TSUN Local: 1511, 02B0, 1097 and experimental 3026.",
)

replace_once(
    'SUPPORTED_PROTOCOLS = ("1511", "02b0", "1097")',
    'VALIDATED_PROTOCOLS = ("1511", "02b0", "1097")\n'
    'EXPERIMENTAL_PROTOCOLS = ("3026",)\n'
    'SUPPORTED_PROTOCOLS = (*VALIDATED_PROTOCOLS, *EXPERIMENTAL_PROTOCOLS)',
)

replace_once(
    'r"(?:^|[_-])(1511|1097|02b0)(?=[_-]|$)", re.IGNORECASE',
    'r"(?:^|[_-])(1511|1097|02b0|3026)(?=[_-]|$)", re.IGNORECASE',
)

replace_once(
    '''    if protocol == "1511":\n        dynamic = [\n''',
    '''    if protocol == "3026":\n        # Experimental read-only candidate family. Keep the capture raw until\n        # the Y4Z hardware mapping is validated on real devices.\n        return split_modbus_range(0x0000, 0x002C), []\n\n    if protocol == "1511":\n        dynamic = [\n''',
)

replace_once(
    '''    elif protocol == "1097":\n        read_modbus_block(\n            host,\n            port,\n            sn,\n            0x1100,\n            0x1100,\n            sensor_list=0x1097,\n            timeout=timeout,\n        )\n    else:\n''',
    '''    elif protocol == "1097":\n        read_modbus_block(\n            host,\n            port,\n            sn,\n            0x1100,\n            0x1100,\n            sensor_list=0x1097,\n            timeout=timeout,\n        )\n    elif protocol == "3026":\n        read_modbus_block(\n            host,\n            port,\n            sn,\n            0x0000,\n            0x0000,\n            sensor_list=0x3026,\n            timeout=timeout,\n        )\n    else:\n''',
)

replace_once(
    '''                sensor_list = 0x1097 if protocol == "1097" else 0\n                values, request_payload, response_payload = read_modbus_block(\n''',
    '''                sensor_list = (\n                    0x1097 if protocol == "1097"\n                    else 0x3026 if protocol == "3026"\n                    else 0\n                )\n                values, request_payload, response_payload = read_modbus_block(\n''',
)

replace_once(
    '''    if protocol == "1097":\n        detected = 0\n        for number in range(1, 7):\n''',
    '''    if protocol == "3026":\n        # The current 3026 capture is intentionally raw-only. Do not infer a PV\n        # count from addresses that may have a different meaning on Y4Z hardware.\n        return 0\n\n    if protocol == "1097":\n        detected = 0\n        for number in range(1, 7):\n''',
)

replace_once(
    '''    else:\n        mapping = {\n            "inverter_status_raw": (0x0BB8, 1),\n''',
    '''    elif protocol == "3026":\n        data.update(\n            {\n                "experimental_protocol": True,\n                "candidate_sensor_list": "0x3026",\n                "mapping_status": "raw_only_pending_hardware_validation",\n            }\n        )\n\n    else:\n        mapping = {\n            "inverter_status_raw": (0x0BB8, 1),\n''',
)

replace_once(
    '''        "1097": "GEN3 / GEN3 PLUS (1097)",\n    }[protocol]\n''',
    '''        "1097": "GEN3 / GEN3 PLUS (1097)",\n        "3026": "GEN3 / GEN3 PLUS (3026 candidate)",\n    }[protocol]\n''',
)

replace_once(
    '''            "detected_protocol": protocol,\n            "model_family": family,\n''',
    '''            "detected_protocol": protocol,\n            "protocol_validation_status": (\n                "experimental_candidate" if protocol == "3026" else "validated"\n            ),\n            "model_family": family,\n''',
)

replace_once(
    '''            "confidence": "direct successful protocol read",\n            "attempts": detection_attempts,\n''',
    '''            "confidence": (\n                "direct successful experimental 3026 read"\n                if protocol == "3026"\n                else "direct successful protocol read"\n            ),\n            "attempts": detection_attempts,\n''',
)

# The generic maintenance patch may already have added SmartLink wording. Match
# only the protocol list so both pre- and post-SmartLink descriptions work.
replace_once(
    '"1511, 02B0 and 1097. Discovery combines UDP, SmartLink UDP, "',
    '"1511, 02B0, 1097 and experimental 3026. Discovery combines UDP, SmartLink UDP, "',
)

path.write_text(text, encoding="utf-8")


test_path = Path("tests/test_tsun_dump_3026.py")
test_path.write_text(
    '''from __future__ import annotations\n\nimport importlib.util\nfrom pathlib import Path\nimport sys\nimport unittest\nfrom unittest.mock import patch\n\n\nTOOL_PATH = Path(__file__).resolve().parents[1] / "tools" / "tsun_dump.py"\nSPEC = importlib.util.spec_from_file_location("tsun_dump_3026_test", TOOL_PATH)\nassert SPEC is not None and SPEC.loader is not None\nTOOL = importlib.util.module_from_spec(SPEC)\nsys.modules[SPEC.name] = TOOL\nSPEC.loader.exec_module(TOOL)\n\n\nclass Experimental3026DiagnosticTests(unittest.TestCase):\n    def test_3026_is_available_to_generic_diagnostic(self) -> None:\n        self.assertIn("3026", TOOL.SUPPORTED_PROTOCOLS)\n        self.assertIn("3026", TOOL.EXPERIMENTAL_PROTOCOLS)\n\n    def test_3026_capture_covers_45_raw_registers(self) -> None:\n        dynamic, supplemental = TOOL.capture_plans("3026", full=True)\n        self.assertEqual(dynamic, [(0x0000, 0x000F), (0x0010, 0x001F), (0x0020, 0x002C)])\n        self.assertEqual(supplemental, [])\n\n    def test_3026_probe_uses_sensor_list_and_fc03_path(self) -> None:\n        with patch.object(TOOL, "read_modbus_block") as reader:\n            reader.return_value = ({0: 1}, b"request", b"response")\n            TOOL._probe_protocol("3026", "192.0.2.10", 8899, 1234567890, 1.0)\n        reader.assert_called_once_with(\n            "192.0.2.10", 8899, 1234567890, 0x0000, 0x0000,\n            sensor_list=0x3026, timeout=1.0\n        )\n\n    def test_3026_decoding_stays_raw_only(self) -> None:\n        decoded = TOOL.decode_known("3026", {"0x0000": 123, "0x0001": 456})\n        self.assertTrue(decoded["experimental_protocol"])\n        self.assertEqual(decoded["candidate_sensor_list"], "0x3026")\n        self.assertEqual(decoded["mapping_status"], "raw_only_pending_hardware_validation")\n        self.assertEqual(decoded["detected_pv_count"], 0)\n        self.assertNotIn("ac_power", decoded)\n        self.assertNotIn("battery_soc", decoded)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
    encoding="utf-8",
)
