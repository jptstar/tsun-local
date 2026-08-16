# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for the protocol-independent TSUN Local decoders."""

from __future__ import annotations

import importlib.util
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch


PROTOCOLS_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tsun_local"
    / "protocols"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_protocol_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_protocol_tests.ap import (  # noqa: E402
    ProtocolTrace,
    TsunProtocolError,
    checksum_ap,
    extract_ap_logger_sn,
    format_ap_frame_for_log,
    parse_ap_frame,
)
from tsun_local_protocol_tests.protocol_02b0 import (  # noqa: E402
    Tsun02b0Client,
    build_modbus_request,
    crc16_modbus,
    decode_alarms as decode_02b0_alarms,
    decode_measurements as decode_02b0,
    detect_pv_count as detect_02b0_pv_count,
    parse_modbus_response,
)
from tsun_local_protocol_tests.protocol_1097 import (  # noqa: E402
    detect_pv_count as detect_1097_pv_count,
)
from tsun_local_protocol_tests.protocol_1511 import (  # noqa: E402
    ALARM_BLOCKS as BLOCKS_1511_ALARM,
    BLOCKS as BLOCKS_1511,
    Tsun1511Client,
    build_1511_request,
    crc16_1511,
    decode_alarms as decode_1511_alarms,
    detect_pv_count as detect_1511_pv_count,
)

DISCOVERY_SPEC = importlib.util.spec_from_file_location(
    "tsun_local_discovery_tests",
    PROTOCOLS_PATH.parent / "discovery.py",
)
assert DISCOVERY_SPEC is not None and DISCOVERY_SPEC.loader is not None
DISCOVERY = importlib.util.module_from_spec(DISCOVERY_SPEC)
DISCOVERY_SPEC.loader.exec_module(DISCOVERY)


def _build_ap_reply(payload: bytes) -> bytes:
    """Build a synthetic valid AP response around a protocol payload."""
    length = 14 + len(payload)
    scope = (
        length.to_bytes(2, "little")
        + b"\x10\x15\x00\x01"
        + b"\x78\x56\x34\x12"
        + b"\x02\x01"
        + bytes(12)
        + payload
    )
    return b"\xA5" + scope + bytes((checksum_ap(scope), 0x15))


class ApFrameTests(unittest.TestCase):
    """Verify the common AP envelope."""

    def test_hides_logger_identifier_in_diagnostic_output(self) -> None:
        octets = format_ap_frame_for_log(bytes(range(16))).split()
        self.assertEqual(octets[7:11], ["XX", "XX", "XX", "XX"])
        self.assertEqual(octets[6], "06")
        self.assertEqual(octets[11], "0B")

    def test_extracts_protocol_payload(self) -> None:
        payload = bytes.fromhex("0103041234ABCD0020")
        self.assertEqual(parse_ap_frame(_build_ap_reply(payload)), payload)

    def test_extracts_logger_identifier_from_ap_envelope(self) -> None:
        self.assertEqual(extract_ap_logger_sn(_build_ap_reply(b"\x01")), 0x12345678)

    def test_rejects_bad_checksum(self) -> None:
        frame = bytearray(_build_ap_reply(b"\x01\x03\x00"))
        frame[-2] ^= 0x01
        with self.assertRaises(TsunProtocolError):
            parse_ap_frame(bytes(frame))

    def test_protocol_trace_is_bounded_and_excludes_connection_data(self) -> None:
        trace = ProtocolTrace("test", max_events=2)
        for start in range(3):
            trace.record(
                function=3,
                start=start,
                end=start,
                stage="connection",
                request_payload=b"\x01\x03",
                error=OSError("connection to 192.0.2.10 failed"),
            )

        self.assertEqual(len(trace.events), 2)
        latest = trace.events[-1]
        self.assertEqual(latest["request_payload"], "01 03")
        self.assertEqual(latest["error"], {"type": "OSError"})
        self.assertNotIn("host", latest)
        self.assertNotIn("logger_sn", latest)


class Protocol02b0Tests(unittest.TestCase):
    """Verify standard Modbus framing and 02B0 register decoding."""

    def test_builds_official_measurement_requests(self) -> None:
        self.assertEqual(
            build_modbus_request(0x03, 0x3009, 0x301E),
            bytes.fromhex("01 03 30 09 00 16 1B 06"),
        )
        self.assertEqual(
            build_modbus_request(0x03, 0x301F, 0x302A),
            bytes.fromhex("01 03 30 1F 00 0C 7B 09"),
        )

    def test_builds_official_alarm_request(self) -> None:
        self.assertEqual(
            build_modbus_request(0x03, 0x3003, 0x3006),
            bytes.fromhex("01 03 30 03 00 04 BB 09"),
        )

    def test_exposes_only_02b0_alarm_entities(self) -> None:
        keys = Tsun02b0Client("192.0.2.10", 8899, 123456).measurement_keys
        self.assertIn("alarm_code_1_raw", keys)
        self.assertIn("alarm_active", keys)
        self.assertNotIn("alarm_global_0_raw", keys)

    def test_parses_big_endian_registers(self) -> None:
        body = bytes.fromhex("01 03 04 12 34 AB CD")
        response = body + crc16_modbus(body)
        self.assertEqual(
            parse_modbus_response(response, 0x03, 0x3009, 0x300A),
            {0x3009: 0x1234, 0x300A: 0xABCD},
        )

    def test_decodes_scaling_type5_and_total_dc_power(self) -> None:
        registers = {address: 0 for address in range(0x3009, 0x302B)}
        registers.update(
            {
                0x3009: 2301,
                0x300A: 123,
                0x300B: 5000,
                0x300F: 4567,
                0x301C: 125,
                0x301D: 1,
                0x301E: 2345,
                0x3010: 410,
                0x3011: 222,
                0x3012: 910,
                0x301F: 150,
                0x3020: 0,
                0x3021: 12345,
                0x3013: 420,
                0x3014: 111,
                0x3015: 800,
                0x3028: 25,
            }
        )
        data = decode_02b0(registers, 4)
        self.assertAlmostEqual(data["ac_voltage"], 230.1)
        self.assertAlmostEqual(data["ac_frequency"], 50.0)
        self.assertAlmostEqual(data["ac_energy_total"], 678.81)
        self.assertAlmostEqual(data["pv1_energy_total"], 123.45)
        self.assertEqual(data["dc_power_total"], 171.0)

    def test_detects_highest_populated_pv_input(self) -> None:
        registers: dict[int, int] = {}
        self.assertEqual(detect_02b0_pv_count(registers), 1)
        registers[0x3014] = 1
        self.assertEqual(detect_02b0_pv_count(registers), 2)
        registers[0x3014] = 0
        registers[0x3029] = 1
        self.assertEqual(detect_02b0_pv_count(registers), 4)
        registers[0x3029] = 0xFFFF
        self.assertEqual(detect_02b0_pv_count(registers), 1)

    def test_exposes_raw_alarm_codes_and_active_state(self) -> None:
        registers = {
            0x3003: 0,
            0x3004: 7,
            0x3005: 0,
            0x3006: 14,
        }
        self.assertEqual(
            decode_02b0_alarms(registers),
            {
                "alarm_code_1_raw": 0,
                "alarm_code_2_raw": 7,
                "alarm_code_3_raw": 0,
                "alarm_code_4_raw": 14,
                "alarm_active": 1,
            },
        )

    def test_alarm_state_requires_complete_alarm_block(self) -> None:
        self.assertEqual(decode_02b0_alarms({0x3003: 1}), {})


class Protocol1511Tests(unittest.TestCase):
    """Protect the validated 1511 request and dynamic PV discovery."""

    def test_builds_validated_ac_request(self) -> None:
        self.assertEqual(
            build_1511_request(0xA1, 0x01, 0x0BB8, 0x0BD0),
            bytes.fromhex("A1 01 00 0B B8 00 02 00 19 C1 FF"),
        )

    def test_builds_validated_secondary_alarm_request(self) -> None:
        self.assertEqual(
            build_1511_request(0xA2, 0x02, 0x0CE4, 0x0CE7),
            bytes.fromhex("A2 02 00 0C E4 00 02 00 04 97 BA"),
        )

    def test_exposes_only_1511_alarm_entities(self) -> None:
        client = Tsun1511Client("192.0.2.10", 8899, 123456)
        keys = client.measurement_keys
        self.assertEqual(client.pv_count, 1)
        self.assertIn("pv1_power", keys)
        self.assertNotIn("pv6_power", keys)
        self.assertIn("alarm_global_0_raw", keys)
        self.assertIn("alarm_secondary_0_raw", keys)
        self.assertIn("pv1_alarm_raw", keys)
        self.assertIn("alarm_active", keys)
        self.assertNotIn("alarm_code_1_raw", keys)

    def test_detects_highest_populated_pv_input(self) -> None:
        self.assertEqual(detect_1511_pv_count({}), 1)
        self.assertEqual(detect_1511_pv_count({0x0EF2: 1}), 5)
        self.assertEqual(detect_1511_pv_count({0x0EF4: 0xFFFF}), 1)
        self.assertEqual(detect_1511_pv_count({0x0EF4: 1}), 6)

    def test_exposes_raw_alarm_words_and_active_state(self) -> None:
        registers = {
            0x0BBB: 0,
            0x0BBC: 2,
            0x0BBD: 0,
            0x0BBE: 0,
            0x0CE4: 0,
            0x0CE5: 0,
            0x0CE6: 0,
            0x0CE7: 0,
            0x0E16: 4,
            0x0E1D: 0,
        }
        self.assertEqual(
            decode_1511_alarms(registers, 2),
            {
                "alarm_global_0_raw": 0,
                "alarm_global_1_raw": 2,
                "alarm_global_2_raw": 0,
                "alarm_global_3_raw": 0,
                "alarm_secondary_0_raw": 0,
                "alarm_secondary_1_raw": 0,
                "alarm_secondary_2_raw": 0,
                "alarm_secondary_3_raw": 0,
                "pv1_alarm_raw": 4,
                "pv2_alarm_raw": 0,
                "alarm_active": 1,
            },
        )

    def test_1511_alarm_state_requires_secondary_block(self) -> None:
        alarms = decode_1511_alarms(
            {0x0BBB: 0, 0x0BBC: 0, 0x0BBD: 0, 0x0BBE: 0, 0x0E16: 0},
            1,
        )
        self.assertNotIn("alarm_active", alarms)


class Protocol1511ClientTests(unittest.IsolatedAsyncioTestCase):
    """Verify one full TITAN transport cycle exposes every PV input."""

    async def test_reads_all_titan_blocks_and_exposes_six_pv_inputs(self) -> None:
        def build_reply(block: tuple[int, int, int, int]) -> bytes:
            address_tag, function, start, end = block
            values = bytes((end - start + 1) * 2)
            body = (
                bytes((address_tag, function | 0x80, 0x01))
                + start.to_bytes(2, "big")
                + len(values).to_bytes(2, "big")
                + values
            )
            return _build_ap_reply(b"\x7E" + body + crc16_1511(body))

        responses = iter(
            build_reply(block) for block in (*BLOCKS_1511, *BLOCKS_1511_ALARM)
        )

        class FakeReader:
            def __init__(self, response: bytes) -> None:
                self.response = response
                self.offset = 0

            async def readexactly(self, size: int) -> bytes:
                result = self.response[self.offset : self.offset + size]
                self.offset += size
                return result

        class FakeWriter:
            def write(self, _request: bytes) -> None:
                pass

            async def drain(self) -> None:
                pass

            def close(self) -> None:
                pass

            async def wait_closed(self) -> None:
                pass

        async def open_connection(_host: str, _port: int):
            return FakeReader(next(responses)), FakeWriter()

        protocol_module = sys.modules["tsun_local_protocol_tests.protocol_1511"]
        with patch.object(
            protocol_module.asyncio, "open_connection", new=open_connection
        ):
            client = Tsun1511Client("192.0.2.10", 8899, 123456)
            result = await client.async_read_all()

        self.assertEqual(result.blocks_ok, 4)
        self.assertEqual(client.pv_count, 1)
        self.assertIn("pv1_power", result.measurements)
        self.assertNotIn("pv6_power", result.measurements)


class Protocol1097DetectionTests(unittest.TestCase):
    """Verify 1097 PV detection never invents six inputs."""

    def test_zero_registers_do_not_default_to_six(self) -> None:
        self.assertEqual(detect_1097_pv_count({}), 0)

    def test_detects_highest_observed_channel(self) -> None:
        self.assertEqual(detect_1097_pv_count({0x1302 + (3 * 7): 1}), 4)
        self.assertEqual(detect_1097_pv_count({0x1302 + (5 * 7): 0xFFFF}), 0)


class AutoProtocolTests(unittest.IsolatedAsyncioTestCase):
    """Verify automatic protocol selection and retention."""

    async def test_selects_working_protocol_and_reuses_it(self) -> None:
        attempts: list[str] = []

        class FakeClient:
            model = "Test"
            pv_count = 1
            measurement_keys = frozenset({"ac_power"})

            def __init__(self, protocol_name: str, succeeds: bool) -> None:
                self.protocol_name = protocol_name
                self.succeeds = succeeds
                self.reads = 0

            @property
            def diagnostic_trace(self):
                return (
                    {
                        "protocol": self.protocol_name,
                        "stage": "complete" if self.succeeds else "validation",
                    },
                )

            async def async_read_all(self):
                self.reads += 1
                if not self.succeeds:
                    raise RuntimeError("wrong protocol")
                return PROTOCOLS.TsunReadResult(
                    measurements={"ac_power": 1},
                    duration_ms=1,
                    blocks_ok=1,
                )

        working_client = FakeClient("02b0", True)

        def create_client(protocol_name: str, *_args):
            attempts.append(protocol_name)
            if protocol_name in {"1511", "1097"}:
                return FakeClient(protocol_name, False)
            return working_client

        with (
            patch.object(
                PROTOCOLS,
                "async_detect_protocol_from_firmware",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                PROTOCOLS, "_create_specific_client", new=create_client
            ),
        ):
            client = PROTOCOLS.TsunAutoClient("192.0.2.10", 8899, 123456)
            await client.async_read_all()
            await client.async_read_all()

        self.assertEqual(attempts, ["1511", "1097", "02b0"])
        self.assertEqual(client.protocol_name, "02b0")
        self.assertEqual(working_client.reads, 2)
        self.assertEqual(client.diagnostic_trace[0]["protocol"], "1511")

    def test_extracts_protocol_from_known_firmware_names(self) -> None:
        self.assertEqual(PROTOCOLS.protocol_from_firmware("LSW5_SSL_1511_1.03"), "1511")
        self.assertEqual(PROTOCOLS.protocol_from_firmware("LSW5BLE_17_02B0_1.08-D1"), "02b0")
        self.assertEqual(PROTOCOLS.protocol_from_firmware("LOGGER_1097_TEST"), "1097")
        self.assertIsNone(PROTOCOLS.protocol_from_firmware("LSW3_15_FFFF_1.0.9E"))

    async def test_firmware_hint_prevents_blind_protocol_probing(self) -> None:
        attempts: list[str] = []

        class FakeClient:
            model = "Test"
            protocol_name = "02b0"
            pv_count = 1
            measurement_keys = frozenset({"ac_power"})
            diagnostic_trace = ()

            async def async_read_all(self):
                return PROTOCOLS.TsunReadResult(measurements={"ac_power": 1}, duration_ms=1, blocks_ok=1)

        def create_client(protocol_name: str, *_args):
            attempts.append(protocol_name)
            return FakeClient()

        with (
            patch.object(PROTOCOLS, "async_detect_protocol_from_firmware", new=AsyncMock(return_value="02b0")),
            patch.object(PROTOCOLS, "_create_specific_client", new=create_client),
        ):
            client = PROTOCOLS.TsunAutoClient("192.0.2.10", 8899, 123456)
            await client.async_read_all()

        self.assertEqual(attempts, ["02b0"])


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    """Verify the bounded TCP discovery helper."""

    def test_parses_lpb_udp_discovery_reply(self) -> None:
        self.assertEqual(
            DISCOVERY.parse_udp_discovery_reply(
                b"192.0.2.42,AABBCCDDEEFF,TESTIDENTIFIER", "192.0.2.42"
            ),
            "192.0.2.42",
        )

    def test_parses_json_udp_discovery_reply(self) -> None:
        self.assertEqual(
            DISCOVERY.parse_udp_discovery_reply(
                b'{"mid":"TEST","mac":"AABBCC","ip":"192.0.2.43"}',
                "192.0.2.43",
            ),
            "192.0.2.43",
        )

    def test_uses_source_for_a11_udp_reply(self) -> None:
        self.assertEqual(
            DISCOVERY.parse_udp_discovery_reply(
                b"HF-A11-TEST", "192.0.2.44"
            ),
            "192.0.2.44",
        )

    def test_ignores_udp_request_echoes(self) -> None:
        for message in DISCOVERY.UDP_DISCOVERY_MESSAGES:
            self.assertIsNone(
                DISCOVERY.parse_udp_discovery_reply(message, "192.0.2.45")
            )

    async def test_udp_candidates_require_open_tcp_port(self) -> None:
        async def discover_udp(targets: set[str]) -> list[str]:
            self.assertIn("255.255.255.255", targets)
            self.assertIn("192.0.2.255", targets)
            return ["192.0.2.10", "198.51.100.7"]

        async def scan_networks(
            _networks: tuple[IPv4Network, ...], _port: int
        ) -> list[str]:
            return ["192.0.2.10"]

        async def scan_hosts(
            hosts: list[IPv4Address], _port: int
        ) -> list[str]:
            self.assertEqual(hosts, [IPv4Address("198.51.100.7")])
            return ["198.51.100.7"]

        async def identify_firmware(host: str) -> str | None:
            return "1511" if host == "192.0.2.10" else None

        with (
            patch.object(DISCOVERY, "async_discover_udp", new=discover_udp),
            patch.object(DISCOVERY, "async_scan_networks", new=scan_networks),
            patch.object(DISCOVERY, "async_scan_hosts", new=scan_hosts),
            patch.object(DISCOVERY, "async_identify_tsun_firmware", new=identify_firmware),
        ):
            hosts = await DISCOVERY.async_discover_devices(
                [IPv4Network("192.0.2.0/24")], 8899
            )

        self.assertEqual(hosts, ["192.0.2.10"])

    def test_rejects_non_tsun_firmware_token(self) -> None:
        self.assertEqual(DISCOVERY.protocol_from_firmware("LSW5_SSL_1511_1.03"), "1511")
        self.assertEqual(DISCOVERY.protocol_from_firmware("LSW5BLE_17_02B0_1.08-D1"), "02b0")
        self.assertIsNone(DISCOVERY.protocol_from_firmware("MW3_16U_5406_1.59"))
        self.assertIsNone(DISCOVERY.protocol_from_firmware("LSW3_15_FFFF_1.0.9E"))

    async def test_finds_only_host_with_open_port(self) -> None:
        class FakeWriter:
            def close(self) -> None:
                pass

            async def wait_closed(self) -> None:
                pass

        async def open_connection(host: str, _port: int) -> tuple[object, FakeWriter]:
            if host == "127.0.0.1":
                return object(), FakeWriter()
            raise ConnectionRefusedError

        with patch.object(
            DISCOVERY.asyncio, "open_connection", new=open_connection
        ):
            hosts = await DISCOVERY.async_scan_hosts(
                [IPv4Address("127.0.0.1"), IPv4Address("127.0.0.2")], 8899
            )

        self.assertEqual(hosts, ["127.0.0.1"])

    async def test_returns_every_open_host_in_address_order(self) -> None:
        class FakeWriter:
            def close(self) -> None:
                pass

            async def wait_closed(self) -> None:
                pass

        async def open_connection(host: str, _port: int) -> tuple[object, FakeWriter]:
            if host in {"192.0.2.2", "192.0.2.10"}:
                return object(), FakeWriter()
            raise ConnectionRefusedError

        with patch.object(DISCOVERY.asyncio, "open_connection", new=open_connection):
            hosts = await DISCOVERY.async_scan_hosts(
                [
                    IPv4Address("192.0.2.10"),
                    IPv4Address("192.0.2.1"),
                    IPv4Address("192.0.2.2"),
                ],
                8899,
            )

        self.assertEqual(hosts, ["192.0.2.2", "192.0.2.10"])

    def test_bounds_large_adapter_network_to_24(self) -> None:
        network = DISCOVERY.bounded_ipv4_network("192.0.2.42", 16)
        self.assertEqual(network, IPv4Network("192.0.2.0/24"))

    def test_rejects_scan_network_larger_than_24(self) -> None:
        with self.assertRaises(ValueError):
            DISCOVERY.parse_discovery_network("192.0.2.0/23")

    def test_ignores_loopback_adapter(self) -> None:
        self.assertIsNone(
            DISCOVERY.bounded_ipv4_network("127.0.0.1", 8)
        )


if __name__ == "__main__":
    unittest.main()
