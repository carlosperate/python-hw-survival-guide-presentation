import asyncio
import sys
import unittest

# Run from a checkout of the port (STICKY): its tests/unix has the fakes.
sys.path[:0] = [__file__.rsplit("/", 3)[0] + "/device", "tests/unix"]
import fakes  # noqa: E402

ble = fakes.BLE()
sys.modules["bluetooth"] = fakes.bluetooth_module(ble)
from deck.app import link_name  # noqa: E402
from deck.lines import Lines  # noqa: E402
from sticky.bleuart import BLEUART  # noqa: E402


class TestLines(unittest.TestCase):
    def setUp(self):
        ble.__init__()
        self.uart = BLEUART()
        self.lines = Lines(self.uart)

    def run_with(self, script):
        async def main():
            task = asyncio.create_task(self.lines.run())
            out = await script()
            task.cancel()
            return out

        return asyncio.run(main())

    def test_newest_complete_line_wins(self):
        async def script():
            ble.connect()
            ble.write(b"eyes 1\neyes ")
            ble.write(b"2\nled ")
            await asyncio.sleep_ms(50)
            return await self.lines.changed()

        self.assertEqual(self.run_with(script), b"eyes 2")

    # A fragment from a page that dropped mustn't prefix the next page's line.
    def test_partial_line_dropped_on_disconnect(self):
        async def script():
            ble.connect()
            ble.write(b"heap ")
            await asyncio.sleep_ms(50)
            # A reconnect at once: the gap, not a poll of connected, drops the fragment.
            ble.disconnect()
            ble.connect()
            ble.write(b"led 1\n")
            await asyncio.sleep_ms(50)
            return await self.lines.changed()

        self.assertEqual(self.run_with(script), b"led 1")

    def test_long_line_ignored(self):
        async def script():
            ble.connect()
            ble.write(b"x" * 70 + b"\nok 1\n")
            await asyncio.sleep_ms(50)
            return await self.lines.changed()

        self.assertEqual(self.run_with(script), b"ok 1")

    # Over several reads, the end of a line too long mustn't pass for a line of its own.
    def test_long_line_refused_whole(self):
        async def script():
            ble.connect()
            for data in (b"x" * 64, b"x" * 64, b"led 1\n"):
                ble.write(data)
                await asyncio.sleep_ms(20)
            return self.lines.state

        self.assertEqual(self.run_with(script), b"")

    def test_connected_follows_the_central(self):
        self.assertFalse(self.lines.connected)
        ble.connect()
        self.assertTrue(self.lines.connected)
        ble.disconnect()
        self.assertFalse(self.lines.connected)

    def test_notify_adds_newline(self):
        ble.connect()
        self.lines.notify(b"drawn")
        self.assertEqual(ble.notified, [b"drawn\n"])

    # The name shares the 31-byte advertisement with the flags (3 bytes) and its header (2).
    def test_link_name(self):
        name = link_name(ble)
        self.assertEqual(name, "sticky-badge-69f2")
        self.assertLessEqual(len(name), 26)
