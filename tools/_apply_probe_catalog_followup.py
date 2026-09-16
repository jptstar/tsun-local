#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUMP = ROOT / "tools" / "tsun_dump.py"
TEST = ROOT / "tests" / "test_tsun_dump_tool.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


source = DUMP.read_text(encoding="utf-8")
old_summary = '''def _summarize_v5_frame(frame: bytes) -> dict[str, Any]:\n    """Summarize a V5 envelope without retaining logger identity bytes."""\n    try:\n        _validate_ap_frame(frame)\n    except Exception as err:\n        return {"valid": False, "error": safe_error_details(err)}\n    control = int.from_bytes(frame[3:5], "little")\n    sequence = int.from_bytes(frame[5:7], "little")\n    return {\n        "valid": True,\n        "control": f"0x{control:04X}",\n        "control_is_command_response": control in V5_COMMAND_RESPONSE_CONTROLS,\n        "sequence": sequence,\n        "frame_type": frame[11] if len(frame) > 11 else None,\n        "status": frame[12] if len(frame) > 12 else None,\n        "payload_bytes": max(0, len(frame) - 27),\n        "logger_identity_stored": False,\n    }\n'''
new_summary = '''def _summarize_v5_frame(frame: bytes) -> dict[str, Any]:\n    """Summarize any V5 envelope without retaining logger identity bytes."""\n    try:\n        if len(frame) < 13 or frame[0] != 0xA5 or frame[-1] != 0x15:\n            raise TsunProtocolError("Invalid V5 frame markers or minimum length")\n        expected = int.from_bytes(frame[1:3], "little") + 13\n        if len(frame) != expected:\n            raise TsunProtocolError("Invalid V5 frame length")\n        if checksum_ap(frame[1:-2]) != frame[-2]:\n            raise TsunProtocolError("Invalid V5 checksum")\n    except Exception as err:\n        return {"valid": False, "error": safe_error_details(err)}\n    control = int.from_bytes(frame[3:5], "little")\n    sequence = int.from_bytes(frame[5:7], "little")\n    is_command_response = control in V5_COMMAND_RESPONSE_CONTROLS\n    return {\n        "valid": True,\n        "control": f"0x{control:04X}",\n        "control_is_command_response": is_command_response,\n        "sequence": sequence,\n        "sequence_low": sequence & 0xFF,\n        "frame_type": frame[11] if len(frame) > 11 else None,\n        "status": frame[12] if len(frame) > 12 else None,\n        "envelope_payload_bytes": int.from_bytes(frame[1:3], "little"),\n        "embedded_payload_bytes": max(0, len(frame) - 27) if is_command_response else None,\n        "logger_identity_stored": False,\n    }\n'''
source = replace_once(source, old_summary, new_summary, "generic V5 summary")

anchor = '''def run_research_probe_catalog(\n    host: str,\n'''
helper = '''def _read_research_v5_command_response(\n    sock: socket.socket,\n    timeout: float,\n    sequence: _V5SequenceState,\n) -> tuple[bytes, list[dict[str, Any]]]:\n    """Read through bounded unsolicited/heartbeat V5 frames to a command reply."""\n    deadline = time.monotonic() + timeout\n    interleaved: list[dict[str, Any]] = []\n    while len(interleaved) < 8:\n        remaining = deadline - time.monotonic()\n        if remaining <= 0:\n            break\n        sock.settimeout(remaining)\n        frame = read_ap_frame(sock)\n        summary = _summarize_v5_frame(frame)\n        if summary.get("valid") and isinstance(summary.get("sequence"), int):\n            sequence.observe(int(summary["sequence"]))\n        if summary.get("control_is_command_response"):\n            return frame, interleaved\n        interleaved.append(summary)\n    raise socket.timeout("No Solarman V5 command response before timeout")\n\n\n'''
source = replace_once(source, anchor, helper + anchor, "V5 response reader insertion")

source = replace_once(
    source,
    '''                    sock.settimeout(probe_timeout)\n                    sock.sendall(request)\n                    frame = read_ap_frame(sock)\n''',
    '''                    sock.settimeout(probe_timeout)\n                    sock.sendall(request)\n                    frame, interleaved = _read_research_v5_command_response(\n                        sock, probe_timeout, sequence\n                    )\n                    if interleaved:\n                        attempt["interleaved_frames"] = interleaved\n''',
    "main V5 command response read",
)

source = replace_once(
    source,
    '''                if summary.get("valid") and isinstance(summary.get("sequence"), int):\n                    sequence.observe(int(summary["sequence"]))\n                if summary.get("control_is_command_response"):\n''',
    '''                if summary.get("valid") and isinstance(summary.get("sequence"), int):\n                    sequence.observe(int(summary["sequence"]))\n                    summary["sequence_low_echo_matches"] = (\n                        int(summary["sequence"]) & 0xFF\n                    ) == (sequence_value & 0xFF)\n                if summary.get("control_is_command_response"):\n''',
    "sequence echo evidence",
)

source = replace_once(
    source,
    '''                        followup_frame = read_ap_frame(sock)\n                        followup_summary = _summarize_v5_frame(followup_frame)\n''',
    '''                        followup_frame, followup_interleaved = (\n                            _read_research_v5_command_response(\n                                sock,\n                                min(probe_timeout, CHARACTERIZATION_MARKER_WAIT),\n                                sequence,\n                            )\n                        )\n                        if followup_interleaved:\n                            attempt["followup_interleaved_frames"] = followup_interleaved\n                        followup_summary = _summarize_v5_frame(followup_frame)\n''',
    "followup V5 response read",
)
DUMP.write_text(source, encoding="utf-8")

tests = TEST.read_text(encoding="utf-8")
new_test = '''\n    def test_v5_summary_accepts_short_heartbeat_envelope(self) -> None:\n        serial = 123456789\n        payload = bytes(10)\n        scope = (\n            len(payload).to_bytes(2, "little")\n            + b"\\x10\\x47"\n            + b"\\x01\\x00"\n            + serial.to_bytes(4, "little")\n            + payload\n        )\n        frame = b"\\xA5" + scope + bytes((TOOL.checksum_ap(scope), 0x15))\n        summary = TOOL._summarize_v5_frame(frame)\n        self.assertTrue(summary["valid"])\n        self.assertEqual(summary["control"], "0x4710")\n        self.assertFalse(summary["control_is_command_response"])\n        self.assertEqual(summary["sequence_low"], 1)\n\n'''
tests = replace_once(
    tests,
    '\n\nif __name__ == "__main__":\n    unittest.main()\n',
    new_test + '\nif __name__ == "__main__":\n    unittest.main()\n',
    "heartbeat test insertion",
)
TEST.write_text(tests, encoding="utf-8")
print("Applied V5 interleaved-frame follow-up")
