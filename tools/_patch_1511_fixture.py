from pathlib import Path

path = Path("tests/test_protocols.py")
source = path.read_text(encoding="utf-8")
old = '''        responses = iter(
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
'''
new = '''        response = b"".join(
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
            return FakeReader(response), FakeWriter()

        protocol_module = sys.modules["tsun_local_protocol_tests.protocol_1511"]
        with patch.object(
            protocol_module.asyncio, "open_connection", new=open_connection
        ):
            client = Tsun1511Client("192.0.2.10", 8899, 123456)
            client._last_diagnostic_read = float("inf")
            result = await client.async_read_all()
'''
if old not in source:
    raise SystemExit("Expected stale 1511 fixture not found")
path.write_text(source.replace(old, new, 1), encoding="utf-8")
