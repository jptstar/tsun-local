from __future__ import annotations

import importlib.util
import ipaddress
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tsun_ota_probe", ROOT / "tools" / "tsun_ota_probe.py")
assert SPEC and SPEC.loader
ota = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ota)

LOGGER = "10.89.10.13"
REMOTE = "203.0.113.50"
DNS = "10.89.10.1"


def _ipv4(src: str, dst: str, proto: int, payload: bytes) -> bytes:
    total = 20 + len(payload)
    header = bytearray(20)
    header[0] = 0x45
    struct.pack_into("!H", header, 2, total)
    header[8] = 64
    header[9] = proto
    header[12:16] = ipaddress.ip_address(src).packed
    header[16:20] = ipaddress.ip_address(dst).packed
    return bytes(header) + payload


def _udp(src_port: int, dst_port: int, payload: bytes) -> bytes:
    return struct.pack("!HHHH", src_port, dst_port, 8 + len(payload), 0) + payload


def _tcp(src_port: int, dst_port: int, payload: bytes) -> bytes:
    header = bytearray(20)
    struct.pack_into("!HH", header, 0, src_port, dst_port)
    header[12] = 5 << 4
    header[13] = 0x18
    return bytes(header) + payload


def _dns_query(name: str) -> bytes:
    qname = b"".join(bytes([len(label)]) + label.encode() for label in name.split(".")) + b"\x00"
    return struct.pack("!HHHHHH", 1, 0x0100, 1, 0, 0, 0) + qname + struct.pack("!HH", 1, 1)


def _client_hello(host: str) -> bytes:
    name = host.encode("ascii")
    sni_entry = b"\x00" + struct.pack("!H", len(name)) + name
    sni_list = struct.pack("!H", len(sni_entry)) + sni_entry
    ext = struct.pack("!HH", 0, len(sni_list)) + sni_list
    body = (
        b"\x03\x03" + b"\x00" * 32 + b"\x00" + struct.pack("!H", 2) + b"\x13\x01" + b"\x01\x00" + struct.pack("!H", len(ext)) + ext
    )
    hs = b"\x01" + len(body).to_bytes(3, "big") + body
    return b"\x16\x03\x01" + struct.pack("!H", len(hs)) + hs


def test_dns_query_is_recorded_without_logger_ip() -> None:
    analyzer = ota.TrafficAnalyzer(LOGGER)
    packet = _ipv4(LOGGER, DNS, 17, _udp(49152, 53, _dns_query("iot.talent-monitoring.com")))
    analyzer.process_ipv4(packet)
    report = analyzer.report(1.0, "any")
    assert report["observations"]["dns_queries"] == [
        {"name": "iot.talent-monitoring.com", "count": 1}
    ]
    assert LOGGER not in str(report)
    assert report["raw_packets_stored"] is False
    assert report["packet_payload_stored"] is False
    assert report["traffic_injected"] is False


def test_private_dns_name_is_redacted() -> None:
    analyzer = ota.TrafficAnalyzer(LOGGER)
    packet = _ipv4(LOGGER, DNS, 17, _udp(49152, 53, _dns_query("secret.home")))
    analyzer.process_ipv4(packet)
    assert analyzer.dns_queries["<private-domain>"] == 1


def test_http_query_string_is_never_stored() -> None:
    analyzer = ota.TrafficAnalyzer(LOGGER)
    payload = (
        b"GET /firmware/LSW5.bin?serial=SECRET&token=ABC HTTP/1.1\r\n"
        b"Host: www.talent-monitoring.com:9002\r\n\r\n"
    )
    packet = _ipv4(LOGGER, REMOTE, 6, _tcp(50000, 9002, payload))
    analyzer.process_ipv4(packet)
    report = analyzer.report(1.0, None)
    req = report["observations"]["http_requests"][0]
    assert req["host"] == "www.talent-monitoring.com"
    assert req["path"] == "/firmware/LSW5.bin"
    assert "SECRET" not in str(report)
    assert "token" not in str(report)


def test_tls_sni_is_observed_without_decrypting_tls() -> None:
    analyzer = ota.TrafficAnalyzer(LOGGER)
    packet = _ipv4(LOGGER, REMOTE, 6, _tcp(51000, 10443, _client_hello("iot.talent-monitoring.com")))
    analyzer.process_ipv4(packet)
    assert analyzer.tls_sni["iot.talent-monitoring.com"] == 1


def test_capture_filter_is_passive_and_excludes_local_polling_port() -> None:
    cmd = ota.build_tcpdump_command("tcpdump", LOGGER, "any")
    joined = " ".join(cmd)
    assert "not port 8899" in joined
    assert "udp port 53" in joined
    assert "-A" not in cmd
    assert "-X" not in cmd
    assert "-w" in cmd and "-" in cmd


def test_http_and_tls_parsers_do_not_accept_random_payload() -> None:
    assert ota._parse_http(b"random bytes") == (None, None, None)
    assert ota._parse_tls_sni(b"random bytes") is None
